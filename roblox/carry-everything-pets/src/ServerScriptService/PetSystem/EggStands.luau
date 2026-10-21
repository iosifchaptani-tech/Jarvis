--[[
	EggStands  (ServerScriptService > PetSystem > EggStands, a ModuleScript)

	Builds one stand per egg: a pedestal with a glowing trim, the blocky egg,
	a sign with the name and price, and a ProximityPrompt ("Open").

	Where the eggs stand:
	  - If Workspace has a Folder "PetEggs" with Parts named like the eggs
	    (StarterEgg, InfernoEgg, CosmicEgg), each egg stands on its Part.
	    The Part becomes invisible; its front (-Z) is where the sign faces.
	  - Otherwise the eggs stand in a row about 24 studs in front of the spawn.
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))
local PetBuilder = require(Shared:WaitForChild("PetBuilder"))
local PetLogic = require(Shared:WaitForChild("PetLogic"))

local EggStands = {}

local positions: { [string]: Vector3 } = {}
local EGG_SCALE = 1.1
local TAG = "PetEggStand"

local function flatLook(cf: CFrame): Vector3
	local look = Vector3.new(cf.LookVector.X, 0, cf.LookVector.Z)
	if look.Magnitude < 0.01 then
		return Vector3.new(0, 0, -1)
	end
	return look.Unit
end

local function findSpawn(): BasePart?
	for _, item in ipairs(Workspace:GetDescendants()) do
		if item:IsA("SpawnLocation") and item.Enabled then
			return item
		end
	end
	return nil
end

local function groundBelow(position: Vector3, ignore: { Instance }): Vector3
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local hit = Workspace:Raycast(position + Vector3.new(0, 12, 0), Vector3.new(0, -120, 0), params)
	if hit then
		return hit.Position
	end
	return position
end

local function block(stand: Model, name: string, size: Vector3, cf: CFrame, color: Color3, material: Enum.Material?): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cf
	part.Color = color
	part.Material = material or Enum.Material.SmoothPlastic
	part.Anchored = true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = stand
	return part
end

local function label(parent: Instance, text: string, color: Color3, position: UDim2, size: UDim2): TextLabel
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Size = size
	l.Position = position
	l.Font = Enum.Font.FredokaOne
	l.Text = text
	l.TextColor3 = color
	l.TextScaled = true
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2.5
	stroke.Color = Color3.fromRGB(10, 12, 24)
	stroke.Parent = l
	l.Parent = parent
	return l
end

local function buildStand(eggId: string, cf: CFrame): Model
	local egg = PetConfig.Eggs[eggId]
	local glow = egg.Colors.Spots[1]
	local stand = Instance.new("Model")
	stand.Name = eggId .. "Stand"

	local base = block(stand, "Base", Vector3.new(9, 1, 9), cf * CFrame.new(0, 0.5, 0), Color3.fromRGB(43, 47, 69))
	local top = block(stand, "Top", Vector3.new(6.5, 1.2, 6.5), cf * CFrame.new(0, 1.6, 0), Color3.fromRGB(59, 63, 85))
	for _, side in ipairs({ -1, 1 }) do
		local a = block(stand, "Trim", Vector3.new(6.9, 0.25, 0.25), cf * CFrame.new(0, 2.25, side * 3.35), glow, Enum.Material.Neon)
		local b = block(stand, "Trim", Vector3.new(0.25, 0.25, 6.9), cf * CFrame.new(side * 3.35, 2.25, 0), glow, Enum.Material.Neon)
		a.CanCollide = false
		b.CanCollide = false
	end
	stand.PrimaryPart = base

	local eggModel = PetBuilder.BuildEgg(eggId, EGG_SCALE)
	eggModel.Name = "Egg"
	-- the egg's PrimaryPart (middle layer) sits 9 "pixels" above the egg's bottom
	eggModel:PivotTo(cf * CFrame.new(0, 2.25 + 9 * 0.25 * EGG_SCALE, 0))
	for _, part in ipairs(eggModel:GetDescendants()) do
		if part:IsA("BasePart") then
			part.CanCollide = false
			part.CanQuery = false
		end
	end
	eggModel.Parent = stand

	local light = Instance.new("PointLight")
	light.Color = glow
	light.Range = 14
	light.Brightness = 1.2
	light.Parent = eggModel.PrimaryPart

	local sparkles = Instance.new("ParticleEmitter")
	sparkles.Texture = PetConfig.Textures.Sparkle
	sparkles.Color = ColorSequence.new(glow, egg.Colors.Spots[2] or glow)
	sparkles.Lifetime = NumberRange.new(1, 1.6)
	sparkles.Speed = NumberRange.new(1, 2.2)
	sparkles.SpreadAngle = Vector2.new(35, 35)
	sparkles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
	sparkles.Transparency = NumberSequence.new(0.1, 1)
	sparkles.LightEmission = 1
	sparkles.LightInfluence = 0
	sparkles.Rate = 5
	sparkles.Parent = top

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "PetEggPrompt"
	prompt.ActionText = "Open"
	prompt.ObjectText = egg.Name
	prompt.HoldDuration = 0
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.MaxActivationDistance = math.max(8, PetConfig.EggRange - 3)
	prompt.RequiresLineOfSight = false
	prompt:SetAttribute("EggId", eggId)
	prompt.Parent = top

	local sign = Instance.new("BillboardGui")
	sign.Name = "EggSign"
	sign.Adornee = eggModel.PrimaryPart
	sign.Size = UDim2.fromScale(8, 2.8)
	sign.StudsOffsetWorldSpace = Vector3.new(0, 4.6, 0)
	sign.MaxDistance = 90
	sign.LightInfluence = 0
	sign.Parent = top
	label(sign, egg.Name, Color3.new(1, 1, 1), UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.56))
	label(sign, PetLogic.Commas(egg.Price) .. " " .. PetConfig.CurrencyName, Color3.fromRGB(255, 213, 74), UDim2.fromScale(0, 0.58), UDim2.fromScale(1, 0.42))

	stand:SetAttribute("EggId", eggId)
	CollectionService:AddTag(stand, TAG)
	pcall(function()
		stand.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	end)
	return stand
end

function EggStands.Build()
	local container = Workspace:FindFirstChild("PetEggStands")
	if container then
		container:Destroy()
	end
	container = Instance.new("Folder")
	container.Name = "PetEggStands"
	container.Parent = Workspace

	local markers = Workspace:FindFirstChild("PetEggs")
	local spawn = findSpawn()
	local count = #PetConfig.EggOrder
	local usedAuto = false

	for i, eggId in ipairs(PetConfig.EggOrder) do
		local cf: CFrame
		local marker = markers and markers:FindFirstChild(eggId)
		if marker and marker:IsA("BasePart") then
			local bottom = marker.Position - Vector3.new(0, marker.Size.Y / 2, 0)
			cf = CFrame.lookAt(bottom, bottom + flatLook(marker.CFrame))
			marker.Transparency = 1
			marker.CanCollide = false
			marker.CanQuery = false
			marker.CanTouch = false
		elseif marker and marker:IsA("Model") then
			local pivot = marker:GetPivot()
			cf = CFrame.lookAt(pivot.Position, pivot.Position + flatLook(pivot))
		else
			usedAuto = true
			local origin, forward
			if spawn then
				forward = flatLook(spawn.CFrame)
				origin = spawn.Position + forward * 24
			else
				forward = Vector3.new(0, 0, -1)
				origin = Vector3.new(0, 0, -30)
			end
			local right = forward:Cross(Vector3.yAxis)
			local spot = origin + right * ((i - (count + 1) / 2) * 13)
			local ground = groundBelow(spot, { container })
			-- the sign faces back towards the spawn
			cf = CFrame.lookAt(ground, ground - Vector3.new(forward.X, 0, forward.Z))
		end
		local stand = buildStand(eggId, cf)
		stand.Parent = container
		positions[eggId] = cf.Position + Vector3.new(0, 2, 0)
	end

	if usedAuto then
		print("[Pets] The eggs stand in a row in front of the spawn. To choose the spot: make a Folder 'PetEggs' in Workspace with Parts named StarterEgg, InfernoEgg and CosmicEgg.")
	end
end

function EggStands.GetPosition(eggId: string): Vector3?
	return positions[eggId]
end

return EggStands
