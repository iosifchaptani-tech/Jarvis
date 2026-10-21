--[[
	PetBuilder  (ReplicatedStorage > PetShared > PetBuilder, a ModuleScript)

	Builds a real 3D pet from the lines in PetModels and adds its aura:
	  - neon outline (Highlight)
	  - energy rings (curved Beams on Attachments that spin and tilt)
	  - an aura shell (ForceField ball)
	  - particles (ParticleEmitters with their own preset per effect)
	  - lightning (Beams that flash between moving Attachments)
	  - orbiting stars / crystals / diamonds
	  - rainbow Trails

	Used on each player's device (the pets that follow players, the menu pictures)
	and by the server (the eggs on their stands).

	Pet object:
	  pet.Model, pet.Root           the Model and its anchored Root part
	  pet:SetCFrame(cframe)         move the whole pet
	  pet:Animate(t, dt, speed, detailed)
	  pet:SetFx(level, rateMultiplier)   0 = no effects, 1 = rings only, 2 = everything
	  pet:SetOutline(on)
	  pet:Destroy()
]]

local PetConfig = require(script.Parent:WaitForChild("PetConfig"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetLogic = require(script.Parent:WaitForChild("PetLogic"))

local PetBuilder = {}

local MATERIALS = {
	P = Enum.Material.SmoothPlastic,
	N = Enum.Material.Neon,
	G = Enum.Material.Glass,
	I = Enum.Material.Ice,
}

local SHAPES = {
	Box = Enum.ParticleEmitterShape.Box,
	Sphere = Enum.ParticleEmitterShape.Sphere,
}
local STYLES = {
	Volume = Enum.ParticleEmitterShapeStyle.Volume,
	Surface = Enum.ParticleEmitterShapeStyle.Surface,
}
local IN_OUT = {
	Outward = Enum.ParticleEmitterShapeInOut.Outward,
	Inward = Enum.ParticleEmitterShapeInOut.Inward,
}
local DIRECTIONS = {
	Top = Enum.NormalId.Top,
	Front = Enum.NormalId.Front,
}

-- Particle looks. Sizes and speeds are in studs and get multiplied by the pet size.
local PRESETS = {
	Sparkles = {
		Texture = "Sparkle", Lifetime = { 0.7, 1.3 }, Speed = { 0.3, 1.2 }, Spread = 180,
		Size = { { 0, 0.3 }, { 0.5, 0.42 }, { 1, 0 } }, Transparency = { { 0, 0.1 }, { 1, 1 } },
		Light = 1, Rotation = { 0, 360 }, RotSpeed = { -90, 90 }, Accel = Vector3.new(0, 0.6, 0), Drag = 1,
		Shape = "Sphere", Style = "Volume", HostScale = 1.15,
	},
	Stars = {
		Texture = "Sparkle", Lifetime = { 1.0, 1.8 }, Speed = { 0.1, 0.5 }, Spread = 180,
		Size = { { 0, 0 }, { 0.35, 0.5 }, { 1, 0 } }, Transparency = { { 0, 0.6 }, { 0.35, 0 }, { 1, 1 } },
		Light = 1, Rotation = { 0, 360 }, RotSpeed = { -40, 40 },
		Shape = "Sphere", Style = "Volume", HostScale = 1.45,
	},
	Snow = {
		Texture = "Sparkle", Lifetime = { 1.2, 2.0 }, Speed = { 0.1, 0.4 }, Spread = 180,
		Size = { { 0, 0.16 }, { 1, 0.1 } }, Transparency = { { 0, 0.15 }, { 0.8, 0.35 }, { 1, 1 } },
		Light = 0.7, Rotation = { 0, 360 }, RotSpeed = { -60, 60 }, Accel = Vector3.new(0, -1.4, 0),
		Shape = "Sphere", Style = "Volume", HostScale = 1.25,
	},
	Flames = {
		Texture = "Fire", Lifetime = { 0.45, 0.8 }, Speed = { 0.8, 1.8 }, Spread = 25,
		Size = { { 0, 0.8 }, { 0.6, 0.55 }, { 1, 0.1 } }, Transparency = { { 0, 0.35 }, { 0.5, 0.45 }, { 1, 1 } },
		Light = 0.85, Rotation = { -180, 180 }, RotSpeed = { -60, 60 }, Accel = Vector3.new(0, 3, 0),
		Shape = "Box", Style = "Volume",
	},
	DarkFlames = {
		Texture = "Fire", Lifetime = { 0.5, 0.9 }, Speed = { 0.6, 1.4 }, Spread = 25,
		Size = { { 0, 0.9 }, { 0.6, 0.6 }, { 1, 0.15 } }, Transparency = { { 0, 0.25 }, { 0.6, 0.4 }, { 1, 1 } },
		Light = 0.1, Rotation = { -180, 180 }, RotSpeed = { -60, 60 }, Accel = Vector3.new(0, 2.5, 0),
		Shape = "Box", Style = "Volume",
	},
	Smoke = {
		Texture = "Smoke", Lifetime = { 1.5, 2.5 }, Speed = { 0.2, 0.5 }, Spread = 30,
		Size = { { 0, 0.8 }, { 1, 2.2 } }, Transparency = { { 0, 0.7 }, { 1, 1 } },
		Light = 0, LightInfluence = 0.3, Rotation = { 0, 360 }, RotSpeed = { -20, 20 }, Accel = Vector3.new(0, 0.4, 0),
		Shape = "Box", Style = "Volume",
	},
	Embers = {
		Texture = "Spark", Lifetime = { 0.8, 1.4 }, Speed = { 1.2, 2.6 }, Spread = 35,
		Size = { { 0, 0.14 }, { 1, 0.04 } }, Transparency = { { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } },
		Light = 1, Accel = Vector3.new(0, 1, 0), Drag = 0.5,
		Shape = "Box", Style = "Volume",
	},
	Pillar = {
		Texture = "Sparkle", Lifetime = { 1.0, 1.6 }, Speed = { 2.5, 4.5 }, Spread = 4,
		Size = { { 0, 0.3 }, { 1, 0 } }, Transparency = { { 0, 0.2 }, { 1, 1 } },
		Light = 1, Shape = "Box", Style = "Volume",
	},
	Diamonds = {
		Texture = "Sparkle", Lifetime = { 0.8, 1.4 }, Speed = { 0.4, 1.0 }, Spread = 180,
		Size = { { 0, 0 }, { 0.3, 0.55 }, { 1, 0 } }, Transparency = { { 0, 0 }, { 1, 0.8 } },
		Light = 1, Rotation = { 0, 360 }, RotSpeed = { -180, 180 },
		Shape = "Sphere", Style = "Volume", HostScale = 1.35,
	},
	Nebula = {
		Texture = "Smoke", Lifetime = { 2.5, 3.5 }, Speed = { 0.1, 0.3 }, Spread = 180,
		Size = { { 0, 1.4 }, { 0.5, 2.4 }, { 1, 2.8 } }, Transparency = { { 0, 1 }, { 0.3, 0.55 }, { 0.7, 0.6 }, { 1, 1 } },
		Light = 1, Rotation = { 0, 360 }, RotSpeed = { -15, 15 },
		Shape = "Sphere", Style = "Volume", HostScale = 1.3,
	},
	VoidPull = {
		Texture = "Sparkle", Lifetime = { 0.7, 1.0 }, Speed = { 2.5, 3.5 }, Spread = 0,
		Size = { { 0, 0.35 }, { 1, 0 } }, Transparency = { { 0, 0.2 }, { 1, 0.9 } },
		Light = 1, Shape = "Sphere", Style = "Surface", InOut = "Inward", HostScale = 2.0,
	},
	Breath = {
		Texture = "Fire", Lifetime = { 0.35, 0.6 }, Speed = { 2, 3.2 }, Spread = 12,
		Size = { { 0, 0.25 }, { 1, 0.7 } }, Transparency = { { 0, 0.3 }, { 1, 1 } },
		Light = 0.9, Direction = "Front", Shape = "Box", Style = "Volume",
	},
}

local RAINBOW = {
	Color3.fromRGB(255, 77, 109),
	Color3.fromRGB(255, 176, 32),
	Color3.fromRGB(255, 225, 77),
	Color3.fromRGB(74, 222, 128),
	Color3.fromRGB(56, 189, 248),
	Color3.fromRGB(167, 139, 250),
}

---------------------------------------------------------------------
-- Small helpers
---------------------------------------------------------------------

local function trySet(instance: Instance, property: string, value: any)
	pcall(function()
		(instance :: any)[property] = value
	end)
end

local function plain(part: BasePart)
	part.Anchored = false
	part.CanCollide = false
	part.CanTouch = false
	part.CanQuery = false
	part.CastShadow = false
	part.Massless = true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
end

local function hiddenPart(name: string, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = Vector3.new(0.2, 0.2, 0.2)
	part.Transparency = 1
	plain(part)
	part.Parent = parent
	return part
end

local function weld(part0: BasePart, part1: BasePart, c0: CFrame): Weld
	local w = Instance.new("Weld")
	w.Part0 = part0
	w.Part1 = part1
	w.C0 = c0
	w.C1 = CFrame.identity
	w.Parent = part1
	return w
end

local function numberSequence(points: { { number } }, multiply: number?): NumberSequence
	local m = multiply or 1
	local keys = {}
	for _, p in ipairs(points) do
		table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2] * m))
	end
	return NumberSequence.new(keys)
end

local function rainbowSequence(fromHue: number?, toHue: number?): ColorSequence
	if fromHue and toHue then
		local keys = {}
		for i = 0, 4 do
			local a = i / 4
			local h = (fromHue + (toHue - fromHue) * a) % 1
			table.insert(keys, ColorSequenceKeypoint.new(a, Color3.fromHSV(h, 0.75, 1)))
		end
		return ColorSequence.new(keys)
	end
	local keys = {}
	for i, c in ipairs(RAINBOW) do
		table.insert(keys, ColorSequenceKeypoint.new((i - 1) / (#RAINBOW - 1), c))
	end
	return ColorSequence.new(keys)
end

local function colorSequence(colors: any): ColorSequence
	if colors == "Rainbow" then
		return rainbowSequence()
	end
	if typeof(colors) == "Color3" then
		return ColorSequence.new(colors)
	end
	if type(colors) == "table" and colors[1] then
		return ColorSequence.new(colors[1], colors[2] or colors[1])
	end
	return ColorSequence.new(Color3.new(1, 1, 1))
end

local function angles(rot: { number }): CFrame
	return CFrame.Angles(math.rad(rot[1]), math.rad(rot[2]), math.rad(rot[3]))
end

---------------------------------------------------------------------
-- Model data (read once per pet type)
---------------------------------------------------------------------

local modelCache = {}

local function modelData(petId: string)
	if modelCache[petId] then
		return modelCache[petId]
	end
	local source = PetModels[petId]
	assert(source, "PetModels has no pet called " .. tostring(petId))
	local parts = PetLogic.ParseModel(source.Parts)
	local minV = Vector3.new(math.huge, math.huge, math.huge)
	local maxV = -minV
	for _, p in ipairs(parts) do
		local cf = CFrame.new(p.Pos[1], p.Pos[2], p.Pos[3]) * angles(p.Rot)
		local half = Vector3.new(p.Size[1], p.Size[2], p.Size[3]) / 2
		for _, sx in ipairs({ -1, 1 }) do
			for _, sy in ipairs({ -1, 1 }) do
				for _, sz in ipairs({ -1, 1 }) do
					local corner = cf * Vector3.new(half.X * sx, half.Y * sy, half.Z * sz)
					minV = minV:Min(corner)
					maxV = maxV:Max(corner)
				end
			end
		end
	end
	local data = {
		Parts = parts,
		Pivots = PetLogic.ExpandPivots(source.Pivots),
		WingAxis = source.WingAxis or "Z",
		Min = minV,
		Max = maxV,
		Center = (minV + maxV) / 2,
	}
	modelCache[petId] = data
	return data
end

-- Size information for a pet at a given scale (used for spacing and the menu pictures).
function PetBuilder.GetInfo(petId: string, scale: number?)
	local data = modelData(petId)
	local s = scale or 1
	local size = (data.Max - data.Min) * s
	return {
		Size = size,
		Center = data.Center * s,
		Bottom = data.Min.Y * s,
		Radius = math.max(size.X, size.Z) / 2,
	}
end

function PetBuilder.DefaultScale(petId: string): number
	local def = PetConfig.Pets[petId]
	return PetConfig.PetScale * ((def and def.Scale) or 1)
end

---------------------------------------------------------------------
-- The pet object
---------------------------------------------------------------------

local Pet = {}
Pet.__index = Pet

function PetBuilder.Build(petId: string, options: { Scale: number?, Fx: boolean? }?)
	local opts = options or {}
	local def = PetConfig.Pets[petId]
	assert(def, "PetConfig has no pet called " .. tostring(petId))
	local data = modelData(petId)
	local scale = opts.Scale or PetBuilder.DefaultScale(petId)

	local model = Instance.new("Model")
	model.Name = petId

	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(0.3, 0.3, 0.3)
	root.Transparency = 1
	plain(root)
	root.Anchored = true
	root.CFrame = CFrame.identity
	root.Parent = model
	model.PrimaryPart = root

	local body = Instance.new("Model")
	body.Name = "Body"
	body.Parent = model

	local self = setmetatable({}, Pet)
	self.Id = petId
	self.Def = def
	self.Model = model
	self.Body = body
	self.Root = root
	self.Scale = scale
	self.WingAxis = data.WingAxis
	self.Phase = math.random() * math.pi * 2
	self.Hinges = {}
	self.PartsByName = {}
	self.Emitters = {}
	self.Beams = {}
	self.Rings = {}
	self.Bolts = {}
	self.Trails = {}
	self.Hosts = {}
	self.FxKey = -1
	self.BoltsOn = false

	local sizeV = (data.Max - data.Min) * scale
	self.Size = sizeV
	self.Center = data.Center * scale
	self.Bottom = data.Min.Y * scale
	self.Radius = math.max(sizeV.X, sizeV.Z) / 2

	-- Hinges for the moving groups (head, tail, wings).
	for group, p in pairs(data.Pivots) do
		local base = CFrame.new(p[1] * scale, p[2] * scale, p[3] * scale)
		local hinge = hiddenPart("Hinge" .. group, body)
		hinge.CFrame = base
		self.Hinges[group] = { Weld = weld(root, hinge, base), Base = base, Part = hinge }
	end

	-- The visible parts.
	for _, p in ipairs(data.Parts) do
		local part: BasePart
		if p.Shape == "W" then
			part = Instance.new("WedgePart")
		else
			part = Instance.new("Part")
		end
		part.Name = p.Name
		part.Size = Vector3.new(p.Size[1], p.Size[2], p.Size[3]) * scale
		part.Color = Color3.fromHex(p.Color)
		part.Material = MATERIALS[p.Mat] or Enum.Material.SmoothPlastic
		part.Transparency = p.Transparency
		if p.Mat == "G" then
			part.Reflectance = 0.12
		end
		plain(part)
		local localCF = CFrame.new(p.Pos[1] * scale, p.Pos[2] * scale, p.Pos[3] * scale) * angles(p.Rot)
		part.CFrame = localCF
		local hinge = self.Hinges[p.Group]
		if hinge then
			weld(hinge.Part, part, hinge.Base:Inverse() * localCF)
		else
			weld(root, part, localCF)
		end
		part.Parent = body
		self.PartsByName[p.Name] = part
	end

	if opts.Fx ~= false then
		self:_buildAura()
	end
	return self
end

function Pet:_host(scaleFactor: number): Part
	local key = math.floor(scaleFactor * 100)
	if self.Hosts[key] then
		return self.Hosts[key]
	end
	local host = hiddenPart("AuraVolume" .. key, self.Model)
	local s = self.Size * 0.85 * scaleFactor
	host.Size = Vector3.new(math.max(s.X, 0.5), math.max(s.Y, 0.5), math.max(s.Z, 0.5))
	host.CFrame = CFrame.new(self.Center)
	weld(self.Root, host, CFrame.new(self.Center))
	self.Hosts[key] = host
	return host
end

function Pet:_groundHost(radius: number): Part
	if self.GroundHost then
		return self.GroundHost
	end
	local host = hiddenPart("AuraGround", self.Model)
	host.Size = Vector3.new(radius * 2, 0.2, radius * 2)
	local cf = CFrame.new(0, self.Bottom - 0.15, 0)
	host.CFrame = cf
	weld(self.Root, host, cf)
	self.GroundHost = host
	return host
end

function Pet:_buildAura()
	local aura = self.Def.Aura or {}
	local scale = self.Scale

	local outline = Instance.new("Highlight")
	outline.Name = "Outline"
	outline.Adornee = self.Body
	outline.DepthMode = Enum.HighlightDepthMode.Occluded
	outline.FillTransparency = 1
	outline.OutlineTransparency = 0
	if typeof(aura.Outline) == "Color3" then
		outline.OutlineColor = aura.Outline
	else
		outline.OutlineColor = Color3.new(1, 1, 1)
	end
	outline.Enabled = false
	outline.Parent = self.Model
	self.Outline = outline
	self.HueCycle = aura.HueCycle == true or aura.Outline == "Rainbow"

	local biggestRing = self.Radius
	for _, ring in ipairs(aura.Rings or {}) do
		biggestRing = math.max(biggestRing, ring.Radius * scale)
	end
	self.AuraRadius = biggestRing

	if aura.Shell then
		local shell = Instance.new("Part")
		shell.Name = "AuraShell"
		shell.Shape = Enum.PartType.Ball
		local d = math.max(self.Size.X, self.Size.Y, self.Size.Z) * (aura.Shell.Size or 1.2)
		shell.Size = Vector3.new(d, d, d)
		shell.Material = Enum.Material.ForceField
		shell.Color = aura.Shell.Color
		shell.Transparency = aura.Shell.Transparency or 0.4
		plain(shell)
		shell.CFrame = CFrame.new(self.Center)
		weld(self.Root, shell, CFrame.new(self.Center))
		shell.Parent = self.Model
		self.Shell = shell
		self.ShellTransparency = shell.Transparency
	end

	for i, ring in ipairs(aura.Rings or {}) do
		self:_buildRing(i, ring)
	end
	for _, spec in ipairs(aura.Particles or {}) do
		self:_buildParticles(spec)
	end
	if aura.Lightning then
		self:_buildLightning(aura.Lightning)
	end
	if aura.Orbiters then
		self:_buildOrbiters(aura.Orbiters)
	end
	if aura.Trails then
		self:_buildTrails(aura.Trails)
	end
end

-- A ring = 4 curved Beams between 4 Attachments on a hidden holder part.
-- Each Beam fades from bright to clear, so the spinning ring looks like 4 comets.
function Pet:_buildRing(index: number, ring)
	local scale = self.Scale
	local radius = ring.Radius * scale
	local base = CFrame.new(0, (ring.Y or 0) * scale, 0)
	local holder = hiddenPart("Ring" .. index, self.Model)
	holder.CFrame = base
	local ringWeld = weld(self.Root, holder, base)

	local segments = 4
	local curve = 4 / 3 * math.tan(math.rad(360 / segments) / 4) * radius
	local attachments = {}
	for s = 0, segments - 1 do
		local a = math.rad(s * 360 / segments)
		local position = Vector3.new(math.cos(a) * radius, 0, math.sin(a) * radius)
		local tangent = Vector3.new(-math.sin(a), 0, math.cos(a))
		local att = Instance.new("Attachment")
		att.Name = "RingPoint" .. s
		att.CFrame = CFrame.fromMatrix(position, tangent, Vector3.yAxis)
		att.Parent = holder
		attachments[s + 1] = att
	end

	local forward = (ring.Spin or 0) >= 0
	local width = (ring.Width or 0.15) * scale
	for s = 1, segments do
		local beam = Instance.new("Beam")
		beam.Name = "RingBeam" .. s
		beam.Attachment0 = attachments[s]
		beam.Attachment1 = attachments[s % segments + 1]
		beam.CurveSize0 = curve
		beam.CurveSize1 = curve
		if ring.Colors == "Rainbow" then
			beam.Color = rainbowSequence((s - 1) / segments, s / segments)
		else
			beam.Color = colorSequence(ring.Colors)
		end
		if forward then
			-- spinning towards Attachment1: the bright head is at the front
			beam.Transparency = numberSequence({ { 0, 0.9 }, { 0.4, 0.35 }, { 1, 0 } })
			beam.Width0 = width * 0.35
			beam.Width1 = width
		else
			beam.Transparency = numberSequence({ { 0, 0 }, { 0.6, 0.35 }, { 1, 0.9 } })
			beam.Width0 = width
			beam.Width1 = width * 0.35
		end
		beam.FaceCamera = true
		beam.LightEmission = 1
		beam.LightInfluence = 0
		beam.Segments = 12
		trySet(beam, "Brightness", 2)
		beam.Parent = holder
		table.insert(self.Beams, beam)
	end

	table.insert(self.Rings, {
		Weld = ringWeld,
		Base = base,
		Tilt = math.rad(ring.Tilt or 0),
		Spin = math.rad(ring.Spin or 0),
		Precess = math.rad(ring.Precess or 0),
		Phase = math.random() * math.pi * 2,
	})
end

function Pet:_buildParticles(spec)
	local preset = PRESETS[spec.Preset]
	if not preset then
		warn("[Pets] Unknown particle preset: " .. tostring(spec.Preset))
		return
	end
	local scale = self.Scale
	local where = spec.Where or "Body"
	local hosts = {}
	local fromModelPart = false
	if where == "Ground" then
		table.insert(hosts, self:_groundHost(math.max(self.Radius * 1.1, 1)))
	elseif string.sub(where, 1, 5) == "Part:" then
		local part = self.PartsByName[string.sub(where, 6)]
		if part then
			table.insert(hosts, part)
			fromModelPart = true
		end
	elseif string.sub(where, 1, 6) == "Parts:" then
		for name in string.gmatch(string.sub(where, 7), "[^,%s]+") do
			local part = self.PartsByName[name]
			if part then
				table.insert(hosts, part)
				fromModelPart = true
			end
		end
	end
	if #hosts == 0 then
		table.insert(hosts, self:_host(preset.HostScale or 1))
		fromModelPart = false
	end

	local rate = (spec.Rate or 5) / #hosts
	local sizeScale = scale * (spec.Size or 1)
	for _, host in ipairs(hosts) do
		local e = Instance.new("ParticleEmitter")
		e.Name = spec.Preset
		e.Texture = PetConfig.Textures[preset.Texture] or PetConfig.Textures.Sparkle
		e.Color = colorSequence(spec.Colors)
		e.Lifetime = NumberRange.new(preset.Lifetime[1], preset.Lifetime[2])
		e.Speed = NumberRange.new(preset.Speed[1] * scale, preset.Speed[2] * scale)
		e.SpreadAngle = Vector2.new(preset.Spread, preset.Spread)
		e.Size = numberSequence(preset.Size, sizeScale)
		e.Transparency = numberSequence(preset.Transparency)
		e.LightEmission = preset.Light or 1
		e.LightInfluence = preset.LightInfluence or 0
		if preset.Rotation then
			e.Rotation = NumberRange.new(preset.Rotation[1], preset.Rotation[2])
		end
		if preset.RotSpeed then
			e.RotSpeed = NumberRange.new(preset.RotSpeed[1], preset.RotSpeed[2])
		end
		e.Acceleration = (preset.Accel or Vector3.zero) * scale
		e.Drag = preset.Drag or 0
		e.EmissionDirection = DIRECTIONS[preset.Direction or "Top"]
		if not fromModelPart then
			trySet(e, "Shape", SHAPES[preset.Shape or "Box"])
			trySet(e, "ShapeStyle", STYLES[preset.Style or "Volume"])
			trySet(e, "ShapeInOut", IN_OUT[preset.InOut or "Outward"])
		end
		trySet(e, "Brightness", 1.5)
		e.Rate = rate
		e.Enabled = false
		e.Parent = host
		table.insert(self.Emitters, { Emitter = e, Rate = rate })
	end
end

-- Lightning: each bolt is 6 Attachments joined by 5 straight Beams.
-- Every strike moves the Attachments to a new zig-zag path for a split second.
function Pet:_buildLightning(spec)
	local holder = hiddenPart("Lightning", self.Model)
	holder.CFrame = CFrame.new(self.Center)
	weld(self.Root, holder, CFrame.new(self.Center))
	for _ = 1, spec.Bolts or 2 do
		local atts, beams = {}, {}
		for i = 1, 6 do
			local att = Instance.new("Attachment")
			att.Parent = holder
			atts[i] = att
		end
		for i = 1, 5 do
			local beam = Instance.new("Beam")
			beam.Attachment0 = atts[i]
			beam.Attachment1 = atts[i + 1]
			beam.Width0 = 0.18 * self.Scale
			beam.Width1 = 0.12 * self.Scale
			beam.Color = ColorSequence.new(Color3.new(1, 1, 1), spec.Color)
			beam.LightEmission = 1
			beam.LightInfluence = 0
			beam.FaceCamera = true
			beam.Segments = 1
			trySet(beam, "Brightness", 3)
			beam.Enabled = false
			beam.Parent = holder
			beams[i] = beam
		end
		table.insert(self.Bolts, {
			Atts = atts,
			Beams = beams,
			Every = spec.Every or { 0.6, 1.4 },
			Next = math.random() * 1.5,
			Off = 0,
		})
	end
	self.BoltRadius = math.max(self.Radius, self.Size.Y / 2) + 1.4 * self.Scale
end

function Pet:_buildOrbiters(spec)
	local scale = self.Scale
	local holder = hiddenPart("Orbit", self.Model)
	local base = CFrame.new(0, (spec.Y or 0.5) * scale, 0)
	holder.CFrame = base
	local orbitWeld = weld(self.Root, holder, base)
	local radius = (spec.Radius or 2.5) * scale
	local size = (spec.Size or 0.3) * scale
	for i = 1, spec.Count or 5 do
		local a = (i - 1) / (spec.Count or 5) * math.pi * 2
		local part = Instance.new("Part")
		part.Name = "Orbiter" .. i
		local rot
		if spec.Kind == "Crystal" then
			part.Size = Vector3.new(size * 0.45, size * 1.3, size * 0.45)
			rot = CFrame.Angles(0, math.rad(45), math.rad(12))
		elseif spec.Kind == "Diamond" then
			part.Size = Vector3.new(size, size, size)
			rot = CFrame.Angles(math.rad(45), 0, math.rad(45))
		else
			part.Size = Vector3.new(size, size, size)
			rot = CFrame.Angles(math.rad(45), math.rad(45), 0)
		end
		part.Material = Enum.Material.Neon
		part.Color = spec.Color or Color3.new(1, 1, 1)
		plain(part)
		local localCF = CFrame.new(math.cos(a) * radius, math.sin(a * 3) * 0.15 * scale, math.sin(a) * radius) * rot
		part.CFrame = base * localCF
		weld(holder, part, localCF)
		part.Parent = self.Model
	end
	self.Orbit = {
		Weld = orbitWeld,
		Base = base,
		Tilt = math.rad(spec.Tilt or 0),
		Speed = math.rad(spec.Speed or 45),
		Bob = spec.Kind == "Crystal",
	}
end

function Pet:_buildTrails(spec)
	for _, name in ipairs(spec.Parts or {}) do
		local part = self.PartsByName[name]
		if part then
			local half = part.Size.X * 0.4
			local a0 = Instance.new("Attachment")
			a0.Position = Vector3.new(-half, 0, 0)
			a0.Parent = part
			local a1 = Instance.new("Attachment")
			a1.Position = Vector3.new(half, 0, 0)
			a1.Parent = part
			local trail = Instance.new("Trail")
			trail.Attachment0 = a0
			trail.Attachment1 = a1
			trail.Lifetime = 0.55
			trail.MinLength = 0.05
			trail.FaceCamera = true
			trail.LightEmission = 1
			trail.LightInfluence = 0
			trail.Color = if spec.Rainbow then rainbowSequence() else colorSequence(spec.Colors)
			trail.Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } })
			trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0.2 } })
			trail.Enabled = false
			trail.Parent = part
			table.insert(self.Trails, trail)
		end
	end
end

---------------------------------------------------------------------
-- Every frame
---------------------------------------------------------------------

function Pet:SetCFrame(cf: CFrame)
	self.Root.CFrame = cf
end

local function strike(self, bolt)
	local r = self.BoltRadius or 3
	local dir = Vector3.new(math.random() * 2 - 1, math.random() * 1.2 - 0.4, math.random() * 2 - 1)
	if dir.Magnitude < 0.05 then
		dir = Vector3.xAxis
	end
	dir = dir.Unit
	local side = dir:Cross(Vector3.yAxis)
	if side.Magnitude < 0.05 then
		side = Vector3.xAxis
	end
	side = side.Unit
	local up = side:Cross(dir).Unit
	local startPos = dir * r * 0.25
	local endPos = dir * r * 1.15
	for i, att in ipairs(bolt.Atts) do
		local f = (i - 1) / (#bolt.Atts - 1)
		local p = startPos:Lerp(endPos, f)
		if i > 1 and i < #bolt.Atts then
			local j = r * 0.18
			p += side * (math.random() * 2 - 1) * j + up * (math.random() * 2 - 1) * j
		end
		att.Position = p
	end
	for _, beam in ipairs(bolt.Beams) do
		beam.Enabled = true
	end
end

-- t: time in seconds, dt: frame time, speed: how fast the owner moves,
-- detailed: false for far pets (only cheap work is done).
function Pet:Animate(t: number, dt: number, speed: number, detailed: boolean)
	if detailed then
		local phase = self.Phase
		local flap
		if self.WingAxis == "Y" then
			flap = math.rad(16 * math.sin(t * 4 + phase) + 6)
		else
			flap = math.rad(22 * math.sin(t * (6 + math.min(speed, 24) * 0.15) + phase) + 8)
		end
		for group, hinge in pairs(self.Hinges) do
			local rot
			if group == "WingL" then
				rot = if self.WingAxis == "Y" then CFrame.Angles(0, flap, 0) else CFrame.Angles(0, 0, flap)
			elseif group == "WingR" then
				rot = if self.WingAxis == "Y" then CFrame.Angles(0, -flap, 0) else CFrame.Angles(0, 0, -flap)
			elseif group == "Tail" then
				rot = CFrame.Angles(0, math.rad(12) * math.sin(t * 3 + phase), 0)
			elseif group == "Head" then
				rot = CFrame.Angles(math.rad(4) * math.sin(t * 2 + phase), 0, 0)
			end
			if rot then
				hinge.Weld.C0 = hinge.Base * rot
			end
		end
	end

	local level = self.FxLevel or 0
	if level >= 1 then
		for _, ring in ipairs(self.Rings) do
			ring.Weld.C0 = ring.Base
				* CFrame.Angles(0, ring.Precess * t + ring.Phase, 0)
				* CFrame.Angles(ring.Tilt, 0, 0)
				* CFrame.Angles(0, ring.Spin * t, 0)
		end
		local orbit = self.Orbit
		if orbit then
			local bob = if orbit.Bob then math.sin(t * 2) * 0.25 * self.Scale else 0
			orbit.Weld.C0 = orbit.Base * CFrame.new(0, bob, 0) * CFrame.Angles(orbit.Tilt, 0, 0) * CFrame.Angles(0, orbit.Speed * t, 0)
		end
	end

	if self.BoltsOn then
		for _, bolt in ipairs(self.Bolts) do
			if bolt.Off > 0 then
				bolt.Off -= dt
				if bolt.Off <= 0 then
					for _, beam in ipairs(bolt.Beams) do
						beam.Enabled = false
					end
				end
			end
			bolt.Next -= dt
			if bolt.Next <= 0 then
				strike(self, bolt)
				bolt.Off = 0.09 + math.random() * 0.06
				bolt.Next = bolt.Every[1] + math.random() * (bolt.Every[2] - bolt.Every[1])
			end
		end
	end

	if self.HueCycle and level >= 1 then
		local h = (t * 0.12) % 1
		if self.Shell then
			self.Shell.Color = Color3.fromHSV(h, 0.5, 1)
		end
		if self.Outline then
			self.Outline.OutlineColor = Color3.fromHSV(h, 0.65, 1)
		end
	end
end

-- level: 0 = no effects, 1 = rings + shell, 2 = everything. rateMultiplier scales the particles.
function Pet:SetFx(level: number, rateMultiplier: number)
	local key = level * 1000 + math.floor(rateMultiplier * 100 + 0.5)
	if key == self.FxKey then
		return
	end
	self.FxKey = key
	self.FxLevel = level
	local particles = level >= 2 and rateMultiplier > 0
	for _, item in ipairs(self.Emitters) do
		item.Emitter.Rate = item.Rate * rateMultiplier
		item.Emitter.Enabled = particles
	end
	for _, beam in ipairs(self.Beams) do
		beam.Enabled = level >= 1
	end
	for _, trail in ipairs(self.Trails) do
		trail.Enabled = level >= 2
	end
	self.BoltsOn = level >= 2 and #self.Bolts > 0
	if not self.BoltsOn then
		for _, bolt in ipairs(self.Bolts) do
			for _, beam in ipairs(bolt.Beams) do
				beam.Enabled = false
			end
		end
	end
	if self.Shell then
		self.Shell.Transparency = if level >= 1 then self.ShellTransparency else 1
	end
end

function Pet:SetOutline(on: boolean)
	if self.Outline and self.Outline.Enabled ~= on then
		self.Outline.Enabled = on
	end
end

-- A short burst when the pet appears.
function Pet:Poof()
	local host = self:_host(1)
	local e = Instance.new("ParticleEmitter")
	e.Texture = PetConfig.Textures.Sparkle
	local aura = self.Def.Aura or {}
	e.Color = if typeof(aura.Outline) == "Color3" then ColorSequence.new(aura.Outline) else rainbowSequence()
	e.Lifetime = NumberRange.new(0.4, 0.7)
	e.Speed = NumberRange.new(4 * self.Scale, 8 * self.Scale)
	e.SpreadAngle = Vector2.new(180, 180)
	e.Size = numberSequence({ { 0, 0.6 }, { 1, 0 } }, self.Scale)
	e.LightEmission = 1
	e.LightInfluence = 0
	e.Drag = 4
	e.Rate = 0
	e.Parent = host
	e:Emit(24)
	task.delay(1, function()
		e:Destroy()
	end)
end

function Pet:Destroy()
	self.Model:Destroy()
end

---------------------------------------------------------------------
-- Blocky eggs (for the egg stands and the hatch animation)
---------------------------------------------------------------------

local EGG_WIDTHS = { 6, 10, 12, 14, 16, 16, 16, 16, 14, 10 } -- top to bottom, in "pixels"

-- Returns a Model whose bottom centre is at (0, 0, 0). Height = 5 studs * scale.
function PetBuilder.BuildEgg(eggId: string, scale: number?): Model
	local egg = PetConfig.Eggs[eggId]
	assert(egg, "PetConfig has no egg called " .. tostring(eggId))
	local s = scale or 1
	local px = 0.25 * s
	local model = Instance.new("Model")
	model.Name = eggId
	local count = #EGG_WIDTHS
	local middle
	for i, w in ipairs(EGG_WIDTHS) do
		local layer = Instance.new("Part")
		layer.Name = "Layer" .. i
		layer.Size = Vector3.new(w * px, 2 * px, w * px)
		layer.CFrame = CFrame.new(0, (count - i) * 2 * px + px, 0)
		layer.Color = egg.Colors.Base
		layer.Material = Enum.Material.SmoothPlastic
		plain(layer)
		layer.Anchored = true
		layer.Parent = model
		if i == 6 then
			middle = layer
		end
	end
	-- glowing spots: { layer, side, offset along the side }
	local spots = { { 3, "F", 1 }, { 5, "R", -2 }, { 6, "F", -4 }, { 8, "L", 2 }, { 7, "B", 3 }, { 2, "B", -1 }, { 9, "F", 3 } }
	for n, spot in ipairs(spots) do
		local layerIndex, side, offset = spot[1], spot[2], spot[3]
		local hw = EGG_WIDTHS[layerIndex] * px / 2
		local y = (count - layerIndex) * 2 * px + px
		local part = Instance.new("Part")
		part.Name = "Spot" .. n
		part.Material = Enum.Material.Neon
		part.Color = egg.Colors.Spots[(n % #egg.Colors.Spots) + 1]
		local depth = 0.12 * s
		if side == "F" or side == "B" then
			part.Size = Vector3.new(2 * px, 1.6 * px, depth)
			local z = (hw + depth / 2 - 0.02 * s) * (if side == "F" then -1 else 1)
			part.CFrame = CFrame.new(offset * px, y, z)
		else
			part.Size = Vector3.new(depth, 1.6 * px, 2 * px)
			local x = (hw + depth / 2 - 0.02 * s) * (if side == "L" then -1 else 1)
			part.CFrame = CFrame.new(x, y, offset * px)
		end
		plain(part)
		part.Anchored = true
		part.Parent = model
	end
	local shine = Instance.new("Part")
	shine.Name = "Shine"
	shine.Material = Enum.Material.Neon
	shine.Color = Color3.new(1, 1, 1)
	shine.Transparency = 0.25
	shine.Size = Vector3.new(2 * px, 4 * px, 0.1 * s)
	local hw5 = EGG_WIDTHS[5] * px / 2 -- layers 5 and 6 are equally wide
	shine.CFrame = CFrame.new(-4 * px, (count - 5) * 2 * px, -hw5 - 0.03 * s)
	plain(shine)
	shine.Anchored = true
	shine.Parent = model
	model.PrimaryPart = middle
	return model
end

return PetBuilder
