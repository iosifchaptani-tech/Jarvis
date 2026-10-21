--!nocheck
-- Tests the real PetService inside the fake Roblox from server_mocks.luau.
-- Run: python tools/run_tests.py

local passed, failed = 0, 0
local function test(name, fn)
	local ok, err = pcall(fn)
	if ok then
		passed += 1
	else
		failed += 1
		print_real("FAIL " .. name .. ": " .. tostring(err))
	end
end
local function eq(a, b, msg)
	if a ~= b then
		error((msg or "") .. " expected " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end
local function has(text, part)
	if type(text) ~= "string" or not string.find(text, part, 1, true) then
		error("expected text with '" .. part .. "', got " .. tostring(text), 2)
	end
end

local PetConfig = require(shared:FindFirstChild("PetConfig"))
local PetService = require(system:FindFirstChild("PetService"))
PetService.Start()

local remotesFolder = ReplicatedStorage:FindFirstChild("PetRemotes")
local requestRemote = remotesFolder:FindFirstChild("PetRequest")
local updateRemote = remotesFolder:FindFirstChild("PetUpdate")

local function call(player, action, arg)
	return requestRemote.OnServerInvoke(player, action, arg)
end
local function last(player, kind)
	for i = #updateRemote.Log, 1, -1 do
		local entry = updateRemote.Log[i]
		if entry.To == player and entry.Args[1] == kind then
			return entry.Args[2]
		end
	end
	return nil
end
local function data(player)
	return last(player, "Data")
end
local function setCoins(player, amount)
	player:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value = amount
end

local ana = makePlayer("Ana")

test("joining gives a ready, empty profile", function()
	join(ana)
	eq(PetService.IsReady(ana), true)
	eq(ana:GetAttribute("PetMultiplier"), 1)
	eq(ana:GetAttribute("PetsEquipped"), "")
	local d = data(ana)
	eq(d.EquippedTotal, 0)
	eq(d.MaxEquip, 4)
	eq(d.Storage, 0)
	eq(d.Saving, true)
end)

test("Studio makes test coins when the game has none", function()
	eq(coins(ana), nil)
	advance(5)
	eq(coins(ana), PetConfig.StudioTestCoins)
end)

test("hatching costs coins and gives an equipped pet", function()
	local ok, result = call(ana, "Hatch", "StarterEgg")
	eq(ok, true, "hatch ok")
	eq(#result.Results, 1)
	local petId = result.Results[1].Pet
	eq(result.Results[1].New, true)
	eq(coins(ana), PetConfig.StudioTestCoins - 250)
	local d = data(ana)
	eq(d.Storage, 1)
	eq(d.EquippedTotal, 1)
	eq(d.Discovered[petId], true)
	eq(ana:GetAttribute("PetsEquipped"), petId)
	eq(ana:GetAttribute("PetMultiplier"), 1 + PetConfig.Pets[petId].Power)
end)

test("there is a short wait between two hatches", function()
	local ok, message = call(ana, "Hatch", "StarterEgg")
	eq(ok, false)
	has(message, "Not so fast")
	advance(1)
	eq((call(ana, "Hatch", "StarterEgg")), true)
end)

test("you must stand near the egg", function()
	advance(1)
	moveTo(ana, 200, 3, 200)
	local ok, message = call(ana, "Hatch", "StarterEgg")
	eq(ok, false)
	has(message, "closer")
	moveTo(ana, 0, 3, -16)
end)

test("open 3 at once", function()
	advance(1)
	local before = coins(ana)
	local ok, result = call(ana, "Hatch3", "StarterEgg")
	eq(ok, true)
	eq(#result.Results, 3)
	eq(coins(ana), before - 750)
	eq(data(ana).Storage, 5)
	eq(data(ana).EquippedTotal, 4, "free slots fill by themselves")
end)

test("not enough coins changes nothing", function()
	advance(1)
	setCoins(ana, 100)
	local ok, message = call(ana, "Hatch", "InfernoEgg")
	eq(ok, false)
	has(message, "5,000")
	eq(coins(ana), 100)
	eq(data(ana).Storage, 5)
	setCoins(ana, 1000000)
end)

test("bad requests are refused", function()
	eq((call(ana, 5)), false)
	eq((call(ana, "Hatch", {})), false)
	eq((call(ana, "Hatch", "GoldenEgg")), false)
	eq((call(ana, "Equip", 7)), false)
	eq((call(ana, "Delete", "NotAPet")), false)
	eq((call(ana, "FlyToTheMoon")), false)
end)

test("test command gives pets; Equip Best picks the strongest", function()
	advance(2)
	ana.Chatted:Fire("!pet give Phoenix 2")
	local d = data(ana)
	eq(d.Counts.Phoenix, 2)
	eq(d.Storage, 7)
	eq((call(ana, "EquipBest")), true)
	local equipped = ana:GetAttribute("PetsEquipped")
	advance(0.3) -- what other players see is updated at most 4 times a second
	equipped = ana:GetAttribute("PetsEquipped")
	eq(string.sub(equipped, 1, 15), "Phoenix,Phoenix")
	eq(data(ana).EquippedTotal, 4)
	assert(ana:GetAttribute("PetMultiplier") >= 21, "two Phoenix give at least x21")
end)

test("Unequip All, then Equip one by one up to the limit", function()
	advance(2)
	eq((call(ana, "UnequipAll")), true)
	eq(data(ana).EquippedTotal, 0)
	eq(ana:GetAttribute("PetMultiplier"), 1)
	eq((call(ana, "Equip", "Phoenix")), true)
	eq((call(ana, "Equip", "Phoenix")), true)
	local ok, message = call(ana, "Equip", "Phoenix")
	eq(ok, false)
	has(message, "No more")
	eq(ana:GetAttribute("PetMultiplier"), 21)
	advance(2)
	for petId, count in pairs(data(ana).Counts) do
		if petId ~= "Phoenix" then
			for _ = 1, count do
				call(ana, "Equip", petId)
			end
		end
	end
	eq(data(ana).EquippedTotal, 4)
	local d = data(ana)
	local spare
	for petId, count in pairs(d.Counts) do
		if (d.Equipped[petId] or 0) < count then
			spare = petId
		end
	end
	local ok2, message2 = call(ana, "Equip", spare)
	eq(ok2, false)
	has(message2, "slots are full")
end)

test("Unequip and Delete", function()
	advance(2)
	eq((call(ana, "Unequip", "Phoenix")), true)
	eq(data(ana).Equipped.Phoenix, 1)
	eq((call(ana, "Unequip", "Angel")), false)
	local before = data(ana).Storage
	eq((call(ana, "Delete", "Phoenix")), true)
	eq(data(ana).Storage, before - 1)
	eq(data(ana).Counts.Phoenix, 1)
	eq(data(ana).Equipped.Phoenix, 1, "the unequipped one is deleted first")
end)

test("Exclusive pets can't be deleted", function()
	advance(2)
	eq(PetService.GivePet(ana, "CrystalKing", 1), 1)
	local ok, message = call(ana, "Delete", "CrystalKing")
	eq(ok, false)
	has(message, "Exclusive")
end)

test("formation is saved on the player", function()
	eq((call(ana, "SetFormation", "Circle")), true)
	advance(0.3)
	eq(ana:GetAttribute("PetFormation"), "Circle")
	eq((call(ana, "SetFormation", "Spiral")), false)
end)

test("too many clicks per second are refused", function()
	advance(2)
	for _ = 1, 12 do
		eq((call(ana, "GetData")), true)
	end
	local ok, message = call(ana, "GetData")
	eq(ok, false)
	has(message, "Too many")
	advance(2)
	eq((call(ana, "GetData")), true)
end)

test("rare results are announced to everyone", function()
	advance(2)
	PetConfig.AnnounceFromOrder = 4 -- Legendary and up, so every Cosmic Egg pet counts
	local before = #updateRemote.Log
	moveTo(ana, 26, 3, -16) -- next to the Cosmic Egg
	eq((call(ana, "Hatch", "CosmicEgg")), true)
	moveTo(ana, 0, 3, -16)
	local announced = false
	for i = before + 1, #updateRemote.Log do
		local entry = updateRemote.Log[i]
		if entry.To == "all" and entry.Args[1] == "Announce" then
			announced = true
			eq(entry.Args[2].Name, "Ana")
		end
	end
	PetConfig.AnnounceFromOrder = 5
	eq(announced, true)
end)

test("full storage blocks hatching", function()
	advance(2)
	local space = PetConfig.MaxStorage - data(ana).Storage
	eq(PetService.GivePet(ana, "SnowFox", space + 5), space)
	eq(data(ana).Storage, PetConfig.MaxStorage)
	local ok, message = call(ana, "Hatch", "StarterEgg")
	eq(ok, false)
	has(message, "storage is full")
end)

test("public API", function()
	eq(PetService.GetMultiplier(ana), ana:GetAttribute("PetMultiplier"))
	eq(#PetService.GetEquipped(ana), 4)
	PetService.SetBonusSlots(ana, 2)
	eq(data(ana).MaxEquip, 6)
	PetService.SetBonusSlots(ana, 0)
	eq(data(ana).MaxEquip, 4)
	eq(PetService.GetOwnedCounts(ana).CrystalKing, 1)
end)

local savedUserId = ana.UserId
local savedCounts

test("leaving saves, joining again loads the same pets", function()
	advance(2)
	ana.Chatted:Fire("!pet reset")
	eq(data(ana).Storage, 0)
	PetService.GivePet(ana, "Phoenix", 2)
	PetService.GivePet(ana, "ShadowCat", 1)
	call(ana, "SetFormation", "V")
	savedCounts = data(ana).Counts
	leave(ana)
	local saved = storeData["Player_" .. savedUserId]
	assert(saved, "nothing saved")
	eq(#saved.Pets, 3)
	eq(saved.Lock, nil, "leaving gives the save lock back")

	local again = makePlayer("Ana")
	again.UserId = savedUserId
	join(again)
	local d = data(again)
	eq(d.Counts.Phoenix, savedCounts.Phoenix)
	eq(d.Counts.ShadowCat, 1)
	eq(d.Formation, "V")
	eq(d.EquippedTotal, 3)
	eq(again:GetAttribute("PetMultiplier"), 25)
	leave(again)
end)

test("game pass: Crystal King is given once", function()
	PetConfig.GamePasses.CrystalKing = 777
	local bo = makePlayer("Bo")
	passOwners[bo.UserId .. ":777"] = true
	join(bo)
	eq(data(bo).Counts.CrystalKing, 1)
	leave(bo)
	local boAgain = makePlayer("Bo")
	boAgain.UserId = bo.UserId
	join(boAgain)
	eq(data(boAgain).Counts.CrystalKing, 1, "not given twice")
	leave(boAgain)
	PetConfig.GamePasses.CrystalKing = 0
end)

test("buying the extra slots pass works at once", function()
	PetConfig.GamePasses.ExtraSlots = 888
	local cy = makePlayer("Cy")
	join(cy)
	eq(data(cy).MaxEquip, 4)
	-- a fake "purchase finished" without really owning the pass gives nothing
	MarketplaceService.PromptGamePassPurchaseFinished:Fire(cy, 888, true)
	advance(7)
	eq(data(cy).MaxEquip, 4)
	MarketplaceService.PromptGamePassPurchaseFinished:Fire(cy, 0, true)
	advance(7)
	eq(data(cy).MaxEquip, 4, "pass id 0 is never a pass")
	passOwners[cy.UserId .. ":888"] = true
	MarketplaceService.PromptGamePassPurchaseFinished:Fire(cy, 888, true)
	eq(data(cy).MaxEquip, 4 + PetConfig.ExtraSlotsAmount)
	leave(cy)
	PetConfig.GamePasses.ExtraSlots = 0
end)

test("if loading fails, the player plays but nothing is saved over their pets", function()
	storeData["Player_5555"] = { Pets = { { Id = "p1", Pet = "Angel" } }, Equipped = { "p1" }, NextId = 2 }
	storeControl.FailGet = true
	local dee = makePlayer("Dee")
	dee.UserId = 5555
	join(dee)
	eq(PetService.IsReady(dee), false, "still trying")
	advance(20)
	eq(PetService.IsReady(dee), true)
	eq(data(dee).Saving, false)
	has(last(dee, "Toast"), "could not load")
	storeControl.FailGet = false
	eq(PetService.GivePet(dee, "SnowFox", 1), 0, "no gifts that could never be saved")
	moveTo(dee, 0, 3, -16)
	local ok, message = call(dee, "Hatch", "StarterEgg")
	eq(ok, false)
	has(message, "rejoin")
	local updates = storeControl.Updates
	leave(dee)
	eq(storeControl.Updates, updates, "must not save")
	eq(storeData["Player_5555"].Pets[1].Pet, "Angel", "old pets kept")
end)

test("leaving while loading does not break anything", function()
	storeControl.FailGet = true
	local eve = makePlayer("Eve")
	join(eve)
	leave(eve)
	advance(20)
	storeControl.FailGet = false
	eq(PetService.IsReady(eve), false)
end)

test("autosave and server shutdown save changed pets", function()
	local fin = makePlayer("Fin")
	join(fin)
	PetService.GivePet(fin, "IceDragon", 1)
	local updates = storeControl.Updates
	advance(PetConfig.AutosaveSeconds + 1)
	assert(storeControl.Updates > updates, "autosave did not save")
	PetService.GivePet(fin, "IceDragon", 1)
	updates = storeControl.Updates
	for _, handler in ipairs(closeHandlers) do
		task.spawn(handler)
	end
	advance(1)
	assert(storeControl.Updates > updates, "shutdown did not save")
	eq(#storeData["Player_" .. fin.UserId].Pets, 2)
end)

test("a change is saved within a few seconds (no waiting for autosave)", function()
	local hal = makePlayer("Hal")
	join(hal)
	PetService.GivePet(hal, "ShadowCat", 1)
	eq(storeData["Player_" .. hal.UserId].Pets, nil, "not saved yet")
	advance(PetConfig.SaveAfterChangeSeconds + 1)
	eq(#storeData["Player_" .. hal.UserId].Pets, 1)
	assert(storeData["Player_" .. hal.UserId].Lock, "the save keeps this server's lock while playing")
	leave(hal)
end)

test("another server still has the player: wait, then load the newest pets", function()
	local ivy = makePlayer("Ivy")
	local key = "Player_" .. ivy.UserId
	storeData[key] = { Pets = { { Id = "p1", Pet = "Angel" } }, NextId = 2, Lock = { Job = "server-B", Time = os.time() } }
	join(ivy)
	eq(PetService.IsReady(ivy), false, "waits for server B")
	-- server B finishes: saves a newer pet list and gives the lock back
	storeData[key] = { Pets = { { Id = "p1", Pet = "Angel" }, { Id = "p2", Pet = "GalaxyWolf" } }, NextId = 3 }
	advance(6)
	eq(PetService.IsReady(ivy), true)
	eq(data(ivy).Storage, 2, "got server B's newest pets")
	eq(storeData[key].Lock.Job, "server-A")
	leave(ivy)
end)

test("a lock left by a crashed server is taken over after a while", function()
	local jo = makePlayer("Jo")
	local key = "Player_" .. jo.UserId
	storeData[key] = { Pets = { { Id = "p1", Pet = "VoidBeast" } }, NextId = 2, Lock = { Job = "crashed", Time = os.time() } }
	join(jo)
	advance(40)
	eq(PetService.IsReady(jo), true)
	eq(data(jo).Counts.VoidBeast, 1)
	leave(jo)
end)

test("if another server took the player over, this server stops saving", function()
	local kim = makePlayer("Kim")
	local key = "Player_" .. kim.UserId
	join(kim)
	PetService.GivePet(kim, "SnowFox", 1)
	storeData[key] = { Pets = { { Id = "p1", Pet = "Phoenix" } }, NextId = 2, Lock = { Job = "server-C", Time = os.time() } }
	advance(PetConfig.SaveAfterChangeSeconds + 1)
	eq(storeData[key].Pets[1].Pet, "Phoenix", "server C's save was not overwritten")
	eq(data(kim).Saving, true)
	leave(kim)
	eq(storeData[key].Lock.Job, "server-C")
end)

test("renamed pets stay in the save", function()
	local lu = makePlayer("Lu")
	local key = "Player_" .. lu.UserId
	storeData[key] = { Pets = { { Id = "p1", Pet = "OldPetName" }, { Id = "p2", Pet = "SnowFox" } }, NextId = 3 }
	join(lu)
	eq(data(lu).Storage, 1)
	PetService.GivePet(lu, "IceDragon", 1)
	leave(lu)
	local saved = storeData[key]
	eq(#saved.Pets, 2)
	eq(saved.Kept[1].Pet, "OldPetName")
end)

test("bonus slots set before the pets load still count", function()
	local mo = makePlayer("Mo")
	PetService.SetBonusSlots(mo, 2)
	join(mo)
	eq(data(mo).MaxEquip, 6)
	leave(mo)
end)

test("in the live game only admins can use test commands", function()
	isStudio = false
	local gus = makePlayer("Gus")
	join(gus)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"
	stats.Parent = gus
	local value = Instance.new("IntValue")
	value.Name = "Coins"
	value.Value = 10
	value.Parent = stats
	gus.Chatted:Fire("!pet coins 5000")
	gus.Chatted:Fire("!pet give Phoenix")
	eq(coins(gus), 10)
	eq(data(gus).Storage, 0)
	isStudio = true
end)

test("no warnings were raised by the normal flows", function()
	local unexpected = {}
	for _, w in ipairs(warnings) do
		if not string.find(w, "mock DataStore is down", 1, true) and not string.find(w, "used by another server", 1, true) then
			table.insert(unexpected, w)
		end
	end
	eq(#unexpected, 0, "warnings: " .. table.concat(unexpected, " | "))
end)

print_real(("%d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("tests failed")
end
