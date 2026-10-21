--[[
	PetService  (ServerScriptService > PetSystem > PetService, a ModuleScript)

	The server side of the pet system. It owns everything that matters:
	coins spent on eggs, the odds, the pet list, equipping and saving.
	Players' devices only ask; the server checks every request.

	Other server scripts in your game can use it:

		local PetService = require(game.ServerScriptService.PetSystem.PetService)
		PetService.GetMultiplier(player)            --> 1 + power of the equipped pets
		PetService.GivePet(player, "Phoenix", 1)    --> gives pets (quests, codes, rewards)
		PetService.GetEquipped(player)              --> { "Phoenix", "ShadowCat", ... }
		PetService.SetBonusSlots(player, 1)         --> extra equip slots (rebirths, VIP ...)
		PetService.SetCurrencyAdapter({ Get = ..., Spend = ..., Give = ... })
		PetService.Changed.Event:Connect(function(player) ... end)

	The multiplier is also on the player: player:GetAttribute("PetMultiplier")

	Saving: one DataStore key per player. A small "lock" in the save says which server is
	using it, so a player who quickly switches servers can never have new pets overwritten
	by an older copy.
]]

local DataStoreService = game:GetService("DataStoreService")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))
local PetLogic = require(Shared:WaitForChild("PetLogic"))
local EggStands = require(script.Parent:WaitForChild("EggStands"))

local PetService = {}
PetService.Changed = Instance.new("BindableEvent") -- fires with (player) after any pet change

local profiles: { [Player]: any } = {}
local pendingBonus: { [Player]: number } = {}
local store: DataStore? = nil
local remotes: any = nil
local currencyAdapter: any = nil
local random = Random.new()
local started = false
local warnedAboutCurrency = false

local LOOK_INTERVAL = 0.25 -- other players' devices rebuild pets at most this often per player
local LOCK_WAITS = 6 -- times to wait 5 s for another server to finish saving (then take over)

local function lockTimeout(): number
	return math.max(150, PetConfig.AutosaveSeconds * 1.5)
end

---------------------------------------------------------------------
-- Coins
---------------------------------------------------------------------

local function currencyValue(player: Player): any
	local stats = player:FindFirstChild("leaderstats")
	if not stats then
		return nil
	end
	local names = { PetConfig.CurrencyName }
	for _, name in ipairs(PetConfig.CurrencyFallbacks or {}) do
		table.insert(names, name)
	end
	for _, name in ipairs(names) do
		local value = stats:FindFirstChild(name)
		if value then
			if value:IsA("IntValue") or value:IsA("NumberValue") then
				return value
			elseif not warnedAboutCurrency then
				warnedAboutCurrency = true
				warn(("[Pets] leaderstats.%s is a %s, not a number. Connect your coins with PetService.SetCurrencyAdapter (see README.md)."):format(name, value.ClassName))
			end
		end
	end
	return nil
end

function PetService.GetBalance(player: Player): number
	if currencyAdapter and currencyAdapter.Get then
		local ok, value = pcall(currencyAdapter.Get, player)
		return if ok then (tonumber(value) or 0) else 0
	end
	local value = currencyValue(player)
	return if value then value.Value else 0
end

local function trySpend(player: Player, amount: number): boolean
	if currencyAdapter and currencyAdapter.Spend then
		local ok, result = pcall(currencyAdapter.Spend, player, amount)
		return ok and result == true
	end
	local value = currencyValue(player)
	if not value or value.Value < amount then
		return false
	end
	value.Value -= amount
	return true
end

local function giveCoins(player: Player, amount: number)
	if currencyAdapter and currencyAdapter.Give then
		pcall(currencyAdapter.Give, player, amount)
		return
	end
	local value = currencyValue(player)
	if value then
		value.Value += amount
	end
end

-- For games that keep coins in their own data instead of leaderstats.
-- adapter = { Get = function(player) return coins end,
--             Spend = function(player, amount) return true/false end,
--             Give = function(player, amount) end }   (Give is only used by the test command)
function PetService.SetCurrencyAdapter(adapter)
	currencyAdapter = adapter
end

-- Studio only: if the game has no coins value, make one so the eggs can be tested.
local function ensureTestCurrency(player: Player)
	if not RunService:IsStudio() then
		return
	end
	task.delay(4, function()
		if player.Parent == nil or currencyAdapter or currencyValue(player) then
			return
		end
		local stats = player:FindFirstChild("leaderstats")
		if stats and stats:FindFirstChild(PetConfig.CurrencyName) then
			return -- there is one, it is just not a number value (warned above)
		end
		if not stats then
			stats = Instance.new("Folder")
			stats.Name = "leaderstats"
			stats.Parent = player
		end
		local coins = Instance.new("IntValue")
		coins.Name = PetConfig.CurrencyName
		coins.Value = PetConfig.StudioTestCoins
		coins.Parent = stats
		print(("[Pets] Studio test: made leaderstats.%s with %d coins (only in Studio)."):format(PetConfig.CurrencyName, PetConfig.StudioTestCoins))
	end)
end

---------------------------------------------------------------------
-- Game passes and slots
---------------------------------------------------------------------

local function ownsPass(player: Player, passId: number?): boolean
	if not passId or passId == 0 then
		return false
	end
	local ok, owns = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, passId)
	end)
	return ok and owns == true
end

local function refreshPasses(player: Player, profile)
	local passes = PetConfig.GamePasses
	profile.Passes = {
		ExtraSlots = ownsPass(player, passes.ExtraSlots),
		CrystalKing = ownsPass(player, passes.CrystalKing),
		TripleHatch = passes.TripleHatch == 0 or ownsPass(player, passes.TripleHatch),
	}
end

local function maxEquip(profile): number
	local extra = if profile.Passes.ExtraSlots then PetConfig.ExtraSlotsAmount else 0
	return PetConfig.MaxEquipped + extra + (profile.BonusSlots or 0)
end

---------------------------------------------------------------------
-- Sending the state to the players
---------------------------------------------------------------------

local function notify(player: Player, text: string)
	if remotes then
		remotes.Update:FireClient(player, "Toast", text)
	end
end

-- The pets other players see. Written at most every LOOK_INTERVAL seconds per player,
-- because every device rebuilds that player's pets when it changes.
local function writeLook(player: Player, profile)
	profile.LastLook = os.clock()
	if player.Parent == nil then
		return
	end
	player:SetAttribute("PetsEquipped", table.concat(PetLogic.EquippedTypes(profile.Data, PetConfig.Pets), ","))
	player:SetAttribute("PetFormation", profile.Data.Formation)
end

local function pushLook(player: Player, profile)
	if profile.LookQueued then
		return
	end
	local waited = os.clock() - (profile.LastLook or -math.huge)
	if waited >= LOOK_INTERVAL then
		writeLook(player, profile)
	else
		profile.LookQueued = true
		task.delay(LOOK_INTERVAL - waited, function()
			profile.LookQueued = false
			writeLook(player, profile)
		end)
	end
end

local function publish(player: Player, profile)
	local data = profile.Data
	local limit = maxEquip(profile)
	while #data.Equipped > limit do
		table.remove(data.Equipped)
	end
	local types = PetLogic.EquippedTypes(data, PetConfig.Pets)
	local multiplier = PetLogic.Multiplier(types, PetConfig.Pets)
	player:SetAttribute("PetMultiplier", multiplier)
	player:SetAttribute("PetCount", #data.Pets)
	pushLook(player, profile)
	local counts, equipped = PetLogic.Counts(data)
	if remotes then
		remotes.Update:FireClient(player, "Data", {
			Counts = counts,
			Equipped = equipped,
			EquippedTotal = #data.Equipped,
			MaxEquip = limit,
			Storage = #data.Pets,
			MaxStorage = PetConfig.MaxStorage,
			Multiplier = multiplier,
			Discovered = data.Discovered,
			Formation = data.Formation,
			Saving = profile.CanSave,
			TripleHatch = profile.Passes.TripleHatch == true,
			Balance = PetService.GetBalance(player),
		})
	end
	PetService.Changed:Fire(player)
end

---------------------------------------------------------------------
-- Saving
---------------------------------------------------------------------

local function dataKey(player: Player): string
	return "Player_" .. player.UserId
end

local function isStudioNoAccess(message: string): boolean
	if not RunService:IsStudio() then
		return false
	end
	return string.find(message, "Studio", 1, true) ~= nil
		or string.find(message, "publish", 1, true) ~= nil
		or string.find(message, "403", 1, true) ~= nil
end

-- Returns: data, canSave, failed
local function loadData(player: Player): (any, boolean, boolean)
	local fresh = PetLogic.NewData(PetConfig.DefaultFormation)
	if not store then
		return fresh, false, not RunService:IsStudio()
	end
	local dataStore = store :: DataStore
	local jobId = game.JobId
	local errors, lockWaits = 0, 0
	while true do
		local loaded, locked = nil, false
		local ok, err = pcall(function()
			dataStore:UpdateAsync(dataKey(player), function(old)
				loaded = old
				locked = false
				if type(old) == "table" and type(old.Lock) == "table" and old.Lock.Job ~= jobId then
					local age = os.time() - (tonumber(old.Lock.Time) or 0)
					if age < lockTimeout() and lockWaits < LOCK_WAITS then
						locked = true
						return nil -- another server still has this player: change nothing
					end
				end
				local new = if type(old) == "table" then old else {}
				new.Lock = { Job = jobId, Time = os.time() }
				return new
			end)
		end)
		if ok and not locked then
			return PetLogic.Sanitize(loaded, PetConfig.Pets, PetConfig.Formations, PetConfig.DefaultFormation), true, false
		elseif ok and locked then
			lockWaits += 1
			task.wait(5)
		else
			local message = tostring(err)
			if isStudioNoAccess(message) then
				warn("[Pets] Saving is off here. In Studio: Home > Game Settings > Security > Enable Studio Access to API Services. (" .. message .. ")")
				return fresh, false, false
			end
			errors += 1
			warn(("[Pets] Loading %s's pets failed (try %d): %s"):format(player.Name, errors, message))
			if errors >= 3 then
				return fresh, false, true
			end
			task.wait(errors * 2)
		end
		if player.Parent == nil then
			return fresh, false, true
		end
	end
end

local function savePayload(data)
	local pets = {}
	for _, pet in ipairs(data.Pets) do
		table.insert(pets, { Id = pet.Id, Pet = pet.Pet })
	end
	local kept = {}
	for _, pet in ipairs(data.Kept or {}) do
		table.insert(kept, { Id = pet.Id, Pet = pet.Pet })
	end
	return {
		Version = 1,
		Pets = pets,
		Kept = kept,
		Equipped = table.clone(data.Equipped),
		NextId = data.NextId,
		Discovered = table.clone(data.Discovered),
		Formation = data.Formation,
		Hatched = data.Hatched,
		Granted = table.clone(data.Granted),
	}
end

local function needsSave(profile): boolean
	return profile.Ready and profile.CanSave and profile.SavedVersion ~= profile.Version
end

-- release = true when the player leaves: the lock is removed so the next server can load at once.
local function saveData(player: Player, profile, release: boolean?): boolean
	if not store or not profile.CanSave or profile.Released then
		return false
	end
	while profile.Saving do
		task.wait(0.1)
	end
	if profile.Released or not profile.CanSave then
		return false
	end
	if not release and not needsSave(profile) then
		return true
	end
	profile.Saving = true
	local dataStore = store :: DataStore
	local jobId = game.JobId
	local version = profile.Version
	local payload = savePayload(profile.Data)
	local saved = false
	for attempt = 1, 3 do
		local stolen = false
		local ok, err = pcall(function()
			dataStore:UpdateAsync(dataKey(player), function(old)
				stolen = false
				if type(old) == "table" and type(old.Lock) == "table" and old.Lock.Job ~= jobId then
					stolen = true
					return nil -- another server has taken over this player: don't overwrite
				end
				payload.Lock = if release then nil else { Job = jobId, Time = os.time() }
				return payload
			end)
		end)
		if ok then
			if stolen then
				profile.CanSave = false
				warn(("[Pets] %s's pets are now used by another server, so this server stops saving them."):format(player.Name))
			else
				profile.SavedVersion = version
				if release then
					profile.Released = true
				end
				saved = true
			end
			break
		end
		warn(("[Pets] Saving %s's pets failed (try %d): %s"):format(player.Name, attempt, tostring(err)))
		task.wait(attempt)
	end
	profile.Saving = false
	return saved
end

-- Save soon after a change (a hatch spends coins: don't wait for the next autosave).
local function scheduleSave(player: Player, profile)
	if profile.SaveQueued or not profile.CanSave then
		return
	end
	profile.SaveQueued = true
	task.delay(PetConfig.SaveAfterChangeSeconds or 12, function()
		profile.SaveQueued = false
		if profiles[player] == profile and needsSave(profile) then
			saveData(player, profile)
		end
	end)
end

local function changed(player: Player, profile)
	profile.Version += 1
	publish(player, profile)
	scheduleSave(player, profile)
end

---------------------------------------------------------------------
-- Pets
---------------------------------------------------------------------

local function addPet(profile, petId: string, ignoreStorage: boolean?): boolean
	local data = profile.Data
	if not ignoreStorage and #data.Pets >= PetConfig.MaxStorage then
		return false
	end
	local id = "p" .. data.NextId
	data.NextId += 1
	table.insert(data.Pets, { Id = id, Pet = petId })
	data.Discovered[petId] = true
	return true
end

local function fillEmptySlots(profile)
	local data = profile.Data
	local limit = maxEquip(profile)
	if #data.Equipped >= limit then
		return
	end
	local set = PetLogic.EquippedSet(data)
	local free = {}
	for _, pet in ipairs(data.Pets) do
		if not set[pet.Id] then
			table.insert(free, pet)
		end
	end
	for _, pet in ipairs(PetLogic.SortStrongest(free, PetConfig.Pets)) do
		if #data.Equipped >= limit then
			break
		end
		table.insert(data.Equipped, pet.Id)
	end
end

local function grantExclusives(profile): boolean
	if profile.Passes.CrystalKing and not profile.Data.Granted.CrystalKing then
		addPet(profile, "CrystalKing", true)
		profile.Data.Granted.CrystalKing = true
		return true
	end
	return false
end

local function announce(player: Player, petId: string)
	local def = PetConfig.Pets[petId]
	local rarity = def and PetConfig.Rarities[def.Rarity]
	if rarity and rarity.Order >= PetConfig.AnnounceFromOrder and remotes then
		remotes.Update:FireAllClients("Announce", { Name = player.DisplayName, Pet = petId })
	end
end

local function hatch(player: Player, profile, eggId: any, amount: any)
	if type(eggId) ~= "string" or not PetConfig.Eggs[eggId] then
		return false, "Unknown egg"
	end
	if profile.LoadFailed then
		return false, "Your pets did not load. Please rejoin before opening eggs."
	end
	local egg = PetConfig.Eggs[eggId]
	local count = if amount == 3 then 3 else 1
	if count == 3 and not profile.Passes.TripleHatch then
		return false, "Opening 3 at once needs the Triple Hatch pass"
	end
	local now = os.clock()
	if now - profile.LastHatch < PetConfig.HatchCooldown then
		return false, "Not so fast!"
	end
	local eggPosition = EggStands.GetPosition(eggId)
	local character = player.Character
	local rootPart = character and character:FindFirstChild("HumanoidRootPart")
	if not eggPosition or not rootPart or ((rootPart :: BasePart).Position - eggPosition).Magnitude > PetConfig.EggRange + 4 then
		return false, "Walk closer to the egg"
	end
	if #profile.Data.Pets + count > PetConfig.MaxStorage then
		return false, ("Your pet storage is full (%d/%d). Delete some pets first."):format(#profile.Data.Pets, PetConfig.MaxStorage)
	end
	local cost = egg.Price * count
	local before = profile.LastHatch
	profile.LastHatch = now -- set before paying, so two quick requests can't both get through
	if not trySpend(player, cost) then
		profile.LastHatch = before
		return false, "You need " .. PetLogic.Commas(cost) .. " " .. PetConfig.CurrencyName
	end

	local results = {}
	for _ = 1, count do
		local petId = PetLogic.PickWeighted(egg.Odds, random:NextNumber())
		local isNew = not profile.Data.Discovered[petId]
		addPet(profile, petId, true)
		table.insert(results, { Pet = petId, New = isNew })
	end
	profile.Data.Hatched += count
	if PetConfig.AutoEquipNew then
		fillEmptySlots(profile)
	end
	changed(player, profile)
	for _, result in ipairs(results) do
		announce(player, result.Pet)
	end
	return true, { Results = results, Balance = PetService.GetBalance(player) }
end

local function handle(player: Player, profile, action: string, arg: any)
	local data = profile.Data
	if action == "GetData" then
		publish(player, profile)
		return true
	elseif action == "Hatch" then
		return hatch(player, profile, arg, nil)
	elseif action == "Hatch3" then
		return hatch(player, profile, arg, 3)
	elseif action == "Equip" then
		if type(arg) ~= "string" or not PetConfig.Pets[arg] then
			return false, "Unknown pet"
		end
		if #data.Equipped >= maxEquip(profile) then
			return false, ("All %d slots are full. Unequip a pet first."):format(maxEquip(profile))
		end
		local id = PetLogic.FindOfType(data, arg, false)
		if not id then
			return false, "No more of this pet to equip"
		end
		table.insert(data.Equipped, id)
		changed(player, profile)
		return true
	elseif action == "Unequip" then
		if type(arg) ~= "string" then
			return false, "Unknown pet"
		end
		local id = PetLogic.FindOfType(data, arg, true)
		if not id then
			return false, "This pet is not equipped"
		end
		PetLogic.RemoveId(data.Equipped, id)
		changed(player, profile)
		return true
	elseif action == "EquipBest" then
		data.Equipped = PetLogic.BestIds(data, PetConfig.Pets, maxEquip(profile))
		changed(player, profile)
		return true
	elseif action == "UnequipAll" then
		table.clear(data.Equipped)
		changed(player, profile)
		return true
	elseif action == "Delete" then
		if type(arg) ~= "string" or not PetConfig.Pets[arg] then
			return false, "Unknown pet"
		end
		local rarity = PetConfig.Rarities[PetConfig.Pets[arg].Rarity]
		if rarity and rarity.NoDelete then
			return false, "Exclusive pets can't be deleted"
		end
		local id = PetLogic.FindOfType(data, arg, false) or PetLogic.FindOfType(data, arg, true)
		if not id then
			return false, "You don't have this pet"
		end
		PetLogic.RemoveId(data.Equipped, id)
		for i, pet in ipairs(data.Pets) do
			if pet.Id == id then
				table.remove(data.Pets, i)
				break
			end
		end
		changed(player, profile)
		return true
	elseif action == "SetFormation" then
		if type(arg) ~= "string" or not table.find(PetConfig.Formations, arg) then
			return false, "Unknown formation"
		end
		data.Formation = arg
		changed(player, profile)
		return true
	elseif action == "BuyPass" then
		local passId = type(arg) == "string" and PetConfig.GamePasses[arg]
		if not passId or passId == 0 then
			return false, "Not for sale yet"
		end
		MarketplaceService:PromptGamePassPurchase(player, passId)
		return true
	end
	return false, "Unknown request"
end

local function onRequest(player: Player, action: any, arg: any)
	if type(action) ~= "string" then
		return false, "Bad request"
	end
	local profile = profiles[player]
	if not profile or not profile.Ready then
		return false, "Your pets are still loading..."
	end
	local now = os.clock()
	if now - profile.WindowStart > 1 then
		profile.WindowStart = now
		profile.Requests = 0
	end
	profile.Requests += 1
	if profile.Requests > 12 then
		return false, "Too many clicks, wait a second"
	end
	return handle(player, profile, action, arg)
end

-- A finished purchase is only trusted after Roblox confirms the player owns the pass.
local function onPassPurchased(player: Player, passId: any, purchased: any)
	if purchased ~= true or type(passId) ~= "number" or passId == 0 then
		return
	end
	local key = nil
	for name, id in pairs(PetConfig.GamePasses) do
		if id ~= 0 and id == passId then
			key = name
		end
	end
	if not key then
		return
	end
	for _ = 1, 3 do
		local profile = profiles[player]
		if not profile or player.Parent == nil then
			return
		end
		if profile.Ready and ownsPass(player, passId) then
			profile.Passes[key] = true
			grantExclusives(profile)
			fillEmptySlots(profile)
			changed(player, profile)
			return
		end
		task.wait(2)
	end
end

---------------------------------------------------------------------
-- Test commands (Studio, or the UserIds in PetConfig.Admins)
---------------------------------------------------------------------

local function isAdmin(player: Player): boolean
	return RunService:IsStudio() or table.find(PetConfig.Admins, player.UserId) ~= nil
end

local function onChat(player: Player, message: string)
	local prefix = string.lower(PetConfig.CommandPrefix)
	if string.sub(string.lower(message), 1, #prefix) ~= prefix or not isAdmin(player) then
		return
	end
	local profile = profiles[player]
	if not profile or not profile.Ready then
		return
	end
	local args = {}
	for word in string.gmatch(string.sub(message, #prefix + 1), "%S+") do
		table.insert(args, word)
	end
	local command = string.lower(args[1] or "")
	if command == "coins" then
		local amount = tonumber(args[2]) or 100000
		giveCoins(player, amount)
		notify(player, "Test: +" .. PetLogic.Commas(amount) .. " " .. PetConfig.CurrencyName)
	elseif command == "give" then
		local amount = tonumber(args[#args])
		local last = if amount then #args - 1 else #args
		local words = {}
		for i = 2, last do
			table.insert(words, args[i])
		end
		local petId = PetLogic.FindPetId(table.concat(words, " "), PetConfig.Pets)
		if not petId then
			notify(player, "Test: no pet called '" .. table.concat(words, " ") .. "'")
			return
		end
		local given = PetService.GivePet(player, petId, math.clamp(amount or 1, 1, 50))
		notify(player, ("Test: got %d x %s"):format(given, PetConfig.Pets[petId].Name))
	elseif command == "reset" then
		profile.Data = PetLogic.NewData(PetConfig.DefaultFormation)
		changed(player, profile)
		notify(player, "Test: all pets removed")
	elseif command == "slots" then
		PetService.SetBonusSlots(player, tonumber(args[2]) or 0)
		notify(player, "Test: bonus slots set")
	else
		notify(player, "Test commands: " .. PetConfig.CommandPrefix .. " coins 100000 | give Phoenix 2 | reset | slots 2")
	end
end

---------------------------------------------------------------------
-- Players joining and leaving
---------------------------------------------------------------------

local function onPlayerAdded(player: Player)
	if profiles[player] then
		return
	end
	local profile = {
		Data = PetLogic.NewData(PetConfig.DefaultFormation),
		Ready = false,
		CanSave = false,
		LoadFailed = false,
		Version = 0,
		SavedVersion = 0,
		LastHatch = -math.huge,
		Requests = 0,
		WindowStart = -math.huge,
		Passes = {},
		BonusSlots = pendingBonus[player] or 0,
	}
	profiles[player] = profile
	player:SetAttribute("PetMultiplier", 1)
	player:SetAttribute("PetsEquipped", "")
	player:SetAttribute("PetFormation", PetConfig.DefaultFormation)
	player.Chatted:Connect(function(message)
		onChat(player, message)
	end)
	ensureTestCurrency(player)

	local data, canSave, failed = loadData(player)
	profile.Data = data
	profile.CanSave = canSave
	profile.LoadFailed = failed
	local function leftAlready(): boolean
		if player.Parent ~= nil and profiles[player] == profile then
			return false
		end
		-- left while loading: write the loaded pets back unchanged to give the save lock back
		profile.Ready = true
		saveData(player, profile, true)
		if profiles[player] == profile then
			profiles[player] = nil
		end
		return true
	end
	if leftAlready() then
		return
	end
	refreshPasses(player, profile)
	if leftAlready() then
		return
	end
	profile.BonusSlots = pendingBonus[player] or profile.BonusSlots

	local dirty = false
	if not failed and #data.Pets == 0 and data.Hatched == 0 and not data.Granted.Starter then
		for _, petId in ipairs(PetConfig.StartingPets) do
			if PetConfig.Pets[petId] then
				addPet(profile, petId, true)
			end
		end
		data.Granted.Starter = true
		dirty = #PetConfig.StartingPets > 0
	end
	if not failed and grantExclusives(profile) then
		dirty = true
	end
	if dirty and PetConfig.AutoEquipNew then
		fillEmptySlots(profile)
	end
	profile.Ready = true
	if dirty then
		changed(player, profile)
	else
		publish(player, profile)
	end
	if failed then
		notify(player, "Your pets could not load. Please rejoin; until then eggs are closed and nothing is saved.")
	end
end

local function onPlayerRemoving(player: Player)
	pendingBonus[player] = nil
	local profile = profiles[player]
	if profile and profile.Ready then
		saveData(player, profile, true)
	end
	if profiles[player] == profile then
		profiles[player] = nil
	end
end

---------------------------------------------------------------------
-- Public API
---------------------------------------------------------------------

function PetService.GetMultiplier(player: Player): number
	local value = player:GetAttribute("PetMultiplier")
	return if type(value) == "number" then value else 1
end

function PetService.GetEquipped(player: Player): { string }
	local profile = profiles[player]
	if not profile then
		return {}
	end
	return PetLogic.EquippedTypes(profile.Data, PetConfig.Pets)
end

function PetService.GetOwnedCounts(player: Player): { [string]: number }
	local profile = profiles[player]
	if not profile then
		return {}
	end
	local counts = PetLogic.Counts(profile.Data)
	return counts
end

-- Gives pets (for quests, codes, rewards). Returns how many were given (storage can be full).
function PetService.GivePet(player: Player, petId: string, amount: number?): number
	local profile = profiles[player]
	if not profile or not profile.Ready or profile.LoadFailed or not PetConfig.Pets[petId] then
		return 0
	end
	local given = 0
	for _ = 1, amount or 1 do
		if addPet(profile, petId, false) then
			given += 1
		end
	end
	if given > 0 then
		if PetConfig.AutoEquipNew then
			fillEmptySlots(profile)
		end
		changed(player, profile)
	end
	return given
end

-- Extra equip slots from your own systems (rebirths, VIP ...). Not saved by the pet system:
-- call it again when the player joins. Works even before the pets have loaded.
function PetService.SetBonusSlots(player: Player, slots: number)
	local value = math.max(0, math.floor(tonumber(slots) or 0))
	pendingBonus[player] = value
	local profile = profiles[player]
	if not profile then
		return
	end
	profile.BonusSlots = value
	if profile.Ready then
		publish(player, profile)
	end
end

function PetService.IsReady(player: Player): boolean
	local profile = profiles[player]
	return profile ~= nil and profile.Ready
end

---------------------------------------------------------------------
-- Start (called once by PetServer)
---------------------------------------------------------------------

function PetService.Start()
	if started then
		return
	end
	started = true

	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(PetConfig.DataStoreName)
	end)
	if ok then
		store = result
	else
		warn("[Pets] Saving is off: " .. tostring(result))
	end

	local folder = ReplicatedStorage:FindFirstChild("PetRemotes")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "PetRemotes"
		folder.Parent = ReplicatedStorage
	end
	local request = folder:FindFirstChild("PetRequest") or Instance.new("RemoteFunction")
	request.Name = "PetRequest"
	request.Parent = folder
	local update = folder:FindFirstChild("PetUpdate") or Instance.new("RemoteEvent")
	update.Name = "PetUpdate"
	update.Parent = folder
	remotes = { Request = request, Update = update }
	request.OnServerInvoke = onRequest

	EggStands.Build()

	MarketplaceService.PromptGamePassPurchaseFinished:Connect(onPassPurchased)

	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in ipairs(Players:GetPlayers()) do
		task.spawn(onPlayerAdded, player)
	end

	task.spawn(function()
		while true do
			task.wait(PetConfig.AutosaveSeconds)
			local list = {}
			for player, profile in pairs(profiles) do
				table.insert(list, { player, profile })
			end
			for _, item in ipairs(list) do
				local player, profile = item[1], item[2]
				-- also refreshes the save lock of players who changed nothing
				if profiles[player] == profile and profile.Ready and profile.CanSave then
					profile.SavedVersion = if needsSave(profile) then profile.SavedVersion else -1
					saveData(player, profile)
					task.wait(0.5)
				end
			end
		end
	end)

	game:BindToClose(function()
		local pending = 0
		for player, profile in pairs(profiles) do
			if profile.Ready and profile.CanSave and not profile.Released then
				pending += 1
				task.spawn(function()
					saveData(player, profile, true)
					pending -= 1
				end)
			end
		end
		local begin = os.clock()
		while pending > 0 and os.clock() - begin < 25 do
			task.wait(0.1)
		end
	end)
end

return PetService
