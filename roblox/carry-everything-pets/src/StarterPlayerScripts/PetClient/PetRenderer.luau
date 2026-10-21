--[[
	PetRenderer  (StarterPlayerScripts > PetClient > PetRenderer, a ModuleScript)

	Draws EVERY player's equipped pets on this device:
	  - reads the "PetsEquipped" and "PetFormation" attributes the server puts on each player
	  - builds the pets locally (nothing is sent over the network every frame, so it is smooth)
	  - flies them behind their owner in a formation, with floating, banking and wing flaps
	  - saves work far away: fewer particles, then no particles, then the pet hides;
	    other players' pets are only built when they come near
	  - limits the neon outlines (Roblox shows at most 31, the game needs some too)
	Also gently spins and bobs the eggs on their stands.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))
local PetBuilder = require(Shared:WaitForChild("PetBuilder"))
local PetLogic = require(Shared:WaitForChild("PetLogic"))

local Renderer = {}
Renderer.FxChanged = Instance.new("BindableEvent")

local localPlayer = Players.LocalPlayer
local container: Folder? = nil
local owners: { [Player]: any } = {}
local fxSetting = "High"
local eggs: { [Instance]: any } = {}
local started = false

local BUILDS_PER_TICK = 3 -- pets built per LOD tick (spreads the work over frames)

local function isPhoneOrTablet(): boolean
	return UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
end

local function lowQualityDevice(): boolean
	local ok, level = pcall(function()
		return UserSettings():GetService("UserGameSettings").SavedQualityLevel
	end)
	if ok and level and level ~= Enum.SavedQualitySetting.Automatic then
		return level.Value <= 3
	end
	return false
end

---------------------------------------------------------------------
-- Effects setting ("High", "Low", "Off")
---------------------------------------------------------------------

function Renderer.GetFxSetting(): string
	return fxSetting
end

local lodNow -- set below

function Renderer.SetFxSetting(setting: string)
	if setting ~= "High" and setting ~= "Low" and setting ~= "Off" then
		return
	end
	fxSetting = setting
	Renderer.FxChanged:Fire(setting)
	if lodNow then
		lodNow()
	end
end

---------------------------------------------------------------------
-- Owners and their pets
---------------------------------------------------------------------

local function setVisible(entry, visible: boolean)
	if entry.Visible == visible or not entry.Pet then
		return
	end
	entry.Visible = visible
	if visible then
		if entry.CF then
			entry.Pet:SetCFrame(entry.CF)
		end
		entry.Pet.Model.Parent = container
		entry.Pet:ClearTrails()
		if entry.New then
			entry.New = false
			entry.Pet:Poof()
		end
	else
		entry.Pet:SetOutline(false)
		entry.Pet.Model.Parent = nil
	end
end

local function parseEquipped(value: any): { string }
	local list = {}
	if type(value) ~= "string" then
		return list
	end
	for petId in string.gmatch(value, "[^,]+") do
		if PetConfig.Pets[petId] then
			table.insert(list, petId)
		end
	end
	return list
end

local function syncOwner(player: Player, owner)
	local wanted = parseEquipped(player:GetAttribute("PetsEquipped"))
	owner.Formation = player:GetAttribute("PetFormation") or PetConfig.DefaultFormation

	local pool = {}
	for _, entry in ipairs(owner.Pets) do
		pool[entry.Id] = pool[entry.Id] or {}
		table.insert(pool[entry.Id], entry)
	end
	local list = {}
	local spacing = 1
	for _, petId in ipairs(wanted) do
		local bucket = pool[petId]
		if bucket and #bucket > 0 then
			table.insert(list, table.remove(bucket, 1))
		else
			-- built later by buildMissing(), only when the owner is near
			table.insert(list, { Id = petId, Pet = nil, Visible = false, New = true, Yaw = 0 })
		end
		local info = PetBuilder.GetInfo(petId, PetBuilder.DefaultScale(petId))
		spacing = math.max(spacing, info.Radius * 1.6)
	end
	for _, bucket in pairs(pool) do
		for _, entry in ipairs(bucket) do
			if entry.Pet then
				entry.Pet:Destroy()
			end
		end
	end
	owner.Pets = list
	owner.Spacing = spacing
	if lodNow then
		lodNow()
	end
end

local function track(player: Player)
	if owners[player] then
		return
	end
	local owner = {
		Player = player,
		Pets = {},
		Formation = PetConfig.DefaultFormation,
		Spacing = 1,
		GroundOffset = 3,
		BodyScale = 1,
		Connections = {},
	}
	owners[player] = owner
	table.insert(owner.Connections, player:GetAttributeChangedSignal("PetsEquipped"):Connect(function()
		syncOwner(player, owner)
	end))
	table.insert(owner.Connections, player:GetAttributeChangedSignal("PetFormation"):Connect(function()
		owner.Formation = player:GetAttribute("PetFormation") or PetConfig.DefaultFormation
	end))
	syncOwner(player, owner)
end

local function untrack(player: Player)
	local owner = owners[player]
	if not owner then
		return
	end
	owners[player] = nil
	for _, connection in ipairs(owner.Connections) do
		connection:Disconnect()
	end
	for _, entry in ipairs(owner.Pets) do
		if entry.Pet then
			entry.Pet:Destroy()
		end
	end
end

-- How far below the HumanoidRootPart the feet are, and how big the character is
-- (lifting games often make characters bigger).
local function measureCharacter(owner, character: Model, rootPart: BasePart)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local halfRoot = rootPart.Size.Y / 2
	if humanoid and humanoid.RigType == Enum.HumanoidRigType.R15 then
		owner.GroundOffset = halfRoot + humanoid.HipHeight
	else
		owner.GroundOffset = halfRoot + 2 * halfRoot -- R6: legs are as long as the torso is tall
	end
	owner.BodyScale = math.max(1, halfRoot)
end

---------------------------------------------------------------------
-- Every frame: follow and animate
---------------------------------------------------------------------

local function update(dt: number)
	dt = math.min(dt, 0.1)
	local t = os.clock()
	local follow = 1 - math.exp(-dt * PetConfig.FollowSmoothness)
	local turn = 1 - math.exp(-dt * 7)

	for player, owner in pairs(owners) do
		local character = player.Character
		local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not rootPart then
			for _, entry in ipairs(owner.Pets) do
				entry.NoOwner = true
				setVisible(entry, false)
				entry.Pos = nil
			end
			continue
		end

		local rootCF = rootPart.CFrame
		local look = Vector3.new(rootCF.LookVector.X, 0, rootCF.LookVector.Z)
		if look.Magnitude < 0.01 then
			look = Vector3.new(0, 0, -1)
		end
		look = look.Unit
		local base = CFrame.lookAt(rootCF.Position, rootCF.Position + look)
		local velocity = rootPart.AssemblyLinearVelocity
		local flat = Vector3.new(velocity.X, 0, velocity.Z)
		local speed = flat.Magnitude
		local facing = if speed > 2 then flat.Unit else look
		local targetYaw = math.atan2(-facing.X, -facing.Z)
		local groundY = rootCF.Position.Y - owner.GroundOffset
		local slots = PetLogic.FormationSlots(owner.Formation, #owner.Pets, owner.Spacing, t)
		local pitch = -math.clamp(speed / 22, 0, 1) * math.rad(14)

		for i, entry in ipairs(owner.Pets) do
			entry.NoOwner = false
			local pet = entry.Pet
			local slot = slots[i]
			if pet and slot then
				local spot = base * Vector3.new(slot[1] * owner.BodyScale, 0, slot[3] * owner.BodyScale)
				local bob = math.sin(t * 2 + pet.Phase) * 0.3
				local target = Vector3.new(spot.X, groundY + 1.2 + PetConfig.FloatHeight + slot[2] - pet.Bottom + bob, spot.Z)
				if not entry.Pos or (entry.Pos - target).Magnitude > 60 then
					entry.Pos = target
					entry.Yaw = targetYaw
					pet:ClearTrails()
				end
				local previous = entry.Pos
				entry.Pos = previous:Lerp(target, follow)
				entry.Yaw = PetLogic.LerpAngle(entry.Yaw, targetYaw, turn)
				-- bank into turns: compare where the pet is going with where it faces
				local move = entry.Pos - previous
				local right = Vector3.new(math.cos(entry.Yaw), 0, -math.sin(entry.Yaw))
				local roll = math.clamp(-move:Dot(right) / math.max(dt, 1e-3) * 0.02, -0.35, 0.35)
				entry.Roll = (entry.Roll or 0) + (roll - (entry.Roll or 0)) * turn
				entry.CF = CFrame.new(entry.Pos) * CFrame.Angles(0, entry.Yaw, 0) * CFrame.Angles(pitch, 0, entry.Roll)
				if entry.Visible then
					pet:SetCFrame(entry.CF)
					pet:Animate(t, dt, speed, entry.Detailed == true)
				end
			end
		end
	end

	-- eggs on their stands: slow spin and bob (only near the camera)
	local camera = Workspace.CurrentCamera
	if camera then
		local camPos = camera.CFrame.Position
		for _, egg in pairs(eggs) do
			if egg.Model.Parent and (egg.Base.Position - camPos).Magnitude < 140 then
				egg.Model:PivotTo(egg.Base * CFrame.new(0, math.sin(t * 1.6) * 0.3, 0) * CFrame.Angles(0, t * 0.7, 0))
			end
		end
	end
end

---------------------------------------------------------------------
-- A few times a second: build near pets, what to show, effects, outlines
---------------------------------------------------------------------

local function buildMissing(camPos: Vector3)
	local budget = BUILDS_PER_TICK
	for player, owner in pairs(owners) do
		local character = player.Character
		local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if rootPart and character then
			measureCharacter(owner, character, rootPart)
			local near = player == localPlayer or (rootPart.Position - camPos).Magnitude < PetConfig.Fx.HideDistance
			if near then
				for _, entry in ipairs(owner.Pets) do
					if not entry.Pet and not entry.Failed and budget > 0 then
						budget -= 1
						local ok, pet = pcall(PetBuilder.Build, entry.Id)
						if ok then
							entry.Pet = pet
						else
							warn("[Pets] Could not build " .. entry.Id .. ": " .. tostring(pet))
							entry.Failed = true
						end
					end
				end
			end
		end
	end
end

local function lod()
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local camPos = camera.CFrame.Position
	buildMissing(camPos)

	local fx = PetConfig.Fx
	local list = {}
	for player, owner in pairs(owners) do
		local mine = player == localPlayer
		for _, entry in ipairs(owner.Pets) do
			if entry.Pet and entry.Pos and not entry.NoOwner then
				table.insert(list, { Entry = entry, Distance = (entry.Pos - camPos).Magnitude, Mine = mine })
			end
		end
	end
	table.sort(list, function(a, b)
		if a.Mine ~= b.Mine then
			return a.Mine
		end
		return a.Distance < b.Distance
	end)

	local particleSlots = fx.MaxParticlePets
	local outlines = if fxSetting == "High" then fx.OutlineBudget elseif fxSetting == "Low" then fx.OutlineBudgetLow else 0
	local baseRate = if fxSetting == "High" then 1 elseif fxSetting == "Low" then fx.LowRate else 0
	for _, item in ipairs(list) do
		local entry, distance = item.Entry, item.Distance
		local visible = distance < fx.HideDistance
		setVisible(entry, visible)
		if visible then
			local level
			if fxSetting == "Off" or distance > fx.RingDistance then
				level = 0
			elseif distance > fx.ParticleDistance or particleSlots <= 0 then
				level = 1
			else
				level = 2
				particleSlots -= 1
			end
			local rate = baseRate * (if item.Mine then 1 else fx.OtherPlayersRate)
			entry.Pet:SetFx(level, rate)
			entry.Detailed = distance < fx.RingDistance
			-- on "Low" only your own pets get outlines
			local outline = outlines > 0 and distance < fx.RingDistance and (fxSetting == "High" or item.Mine)
			if outline then
				outlines -= 1
			end
			entry.Pet:SetOutline(outline)
		end
	end
end
lodNow = lod

---------------------------------------------------------------------
-- Eggs
---------------------------------------------------------------------

local function addEgg(stand: Instance)
	if eggs[stand] then
		return
	end
	local model = stand:WaitForChild("Egg", 10)
	if model and model:IsA("Model") then
		eggs[stand] = { Model = model, Base = model:GetPivot() }
	end
end

local function removeEgg(stand: Instance)
	eggs[stand] = nil
end

---------------------------------------------------------------------
-- Start
---------------------------------------------------------------------

function Renderer.Start()
	if started then
		return
	end
	started = true

	if (PetConfig.Fx.PhonesStartLow and isPhoneOrTablet()) or lowQualityDevice() then
		fxSetting = "Low"
	end

	local folder = Instance.new("Folder")
	folder.Name = "LocalPets"
	folder.Parent = Workspace
	container = folder

	for _, player in ipairs(Players:GetPlayers()) do
		track(player)
	end
	Players.PlayerAdded:Connect(track)
	Players.PlayerRemoving:Connect(untrack)

	for _, stand in ipairs(CollectionService:GetTagged("PetEggStand")) do
		task.spawn(addEgg, stand)
	end
	CollectionService:GetInstanceAddedSignal("PetEggStand"):Connect(addEgg)
	CollectionService:GetInstanceRemovedSignal("PetEggStand"):Connect(removeEgg)

	RunService.RenderStepped:Connect(update)
	task.spawn(function()
		while true do
			lod()
			task.wait(0.25)
		end
	end)
end

return Renderer
