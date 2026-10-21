--[[
	UIKit  (StarterPlayerScripts > PetClient > UIKit, a ModuleScript)

	Small helpers so the pet menus all look the same: colors, rounded frames,
	buttons that squish when pressed, simple icons drawn from frames (no image
	uploads needed), 3D pictures in ViewportFrames, and screen-size scaling.
]]

local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))

local UIKit = {}

UIKit.Font = Enum.Font.FredokaOne
UIKit.BodyFont = Enum.Font.GothamMedium

UIKit.C = {
	Panel = Color3.fromRGB(20, 26, 48),
	Panel2 = Color3.fromRGB(14, 20, 40),
	Chip = Color3.fromRGB(30, 42, 77),
	Border = Color3.fromRGB(44, 55, 96),
	CardBorder = Color3.fromRGB(34, 43, 71),
	Text = Color3.fromRGB(255, 255, 255),
	Muted = Color3.fromRGB(169, 180, 214),
	Green = Color3.fromRGB(22, 163, 74),
	GreenBright = Color3.fromRGB(34, 197, 94),
	Red = Color3.fromRGB(220, 38, 38),
	RedBright = Color3.fromRGB(239, 68, 68),
	DarkRed = Color3.fromRGB(127, 29, 29),
	Grey = Color3.fromRGB(71, 85, 105),
	Blue = Color3.fromRGB(37, 99, 235),
	Orange = Color3.fromRGB(255, 138, 31),
	Gold = Color3.fromRGB(255, 213, 74),
	GoldDark = Color3.fromRGB(58, 42, 6),
	Unknown = Color3.fromRGB(59, 71, 112),
}

-- UIKit.make("Frame", { Size = ..., Parent = ... }, { children })
function UIKit.make(className: string, props: { [string]: any }?, children: { Instance }?): any
	local instance: any = Instance.new(className)
	local parent = nil
	for key, value in pairs(props or {}) do
		if key == "Parent" then
			parent = value
		else
			instance[key] = value
		end
	end
	for _, child in ipairs(children or {}) do
		child.Parent = instance
	end
	if instance:IsA("GuiObject") and (props == nil or props.BorderSizePixel == nil) then
		instance.BorderSizePixel = 0
	end
	if parent then
		instance.Parent = parent
	end
	return instance
end

function UIKit.corner(parent: Instance, radius: number, scale: number?): UICorner
	return UIKit.make("UICorner", { CornerRadius = UDim.new(scale or 0, radius), Parent = parent })
end

function UIKit.stroke(parent: Instance, color: Color3, thickness: number, forText: boolean?): UIStroke
	return UIKit.make("UIStroke", {
		Color = color,
		Thickness = thickness,
		ApplyStrokeMode = if forText then Enum.ApplyStrokeMode.Contextual else Enum.ApplyStrokeMode.Border,
		Parent = parent,
	})
end

function UIKit.frame(props: { [string]: any }): Frame
	local p = table.clone(props)
	if p.BackgroundColor3 == nil and p.BackgroundTransparency == nil then
		p.BackgroundTransparency = 1
	end
	return UIKit.make("Frame", p)
end

function UIKit.text(props: { [string]: any }): TextLabel
	local p = table.clone(props)
	p.BackgroundTransparency = p.BackgroundTransparency or 1
	p.Font = p.Font or UIKit.Font
	p.TextColor3 = p.TextColor3 or UIKit.C.Text
	p.TextSize = p.TextSize or 16
	return UIKit.make("TextLabel", p)
end

-- A button that squishes when pressed. onClick works for mouse, touch and gamepad.
function UIKit.button(props: { [string]: any }, onClick: (() -> ())?): TextButton
	local p = table.clone(props)
	p.AutoButtonColor = false
	p.Font = p.Font or UIKit.Font
	p.TextColor3 = p.TextColor3 or UIKit.C.Text
	p.TextSize = p.TextSize or 18
	local radius = p.Radius or 12
	p.Radius = nil
	local button = UIKit.make("TextButton", p)
	UIKit.corner(button, radius)
	local scale = UIKit.make("UIScale", { Parent = button })
	local function to(value: number)
		TweenService:Create(scale, TweenInfo.new(0.08, Enum.EasingStyle.Quad), { Scale = value }):Play()
	end
	button.MouseButton1Down:Connect(function()
		to(0.93)
	end)
	button.MouseButton1Up:Connect(function()
		to(1)
	end)
	button.MouseLeave:Connect(function()
		to(1)
	end)
	if onClick then
		button.Activated:Connect(onClick)
	end
	return button
end

function UIKit.tween(instance: Instance, seconds: number, goal: { [string]: any }, style: Enum.EasingStyle?, direction: Enum.EasingDirection?): Tween
	local tween = TweenService:Create(instance, TweenInfo.new(seconds, style or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out), goal)
	tween:Play()
	return tween
end

---------------------------------------------------------------------
-- Icons drawn from frames
---------------------------------------------------------------------

local function dot(parent: Instance, x: number, y: number, w: number, h: number, color: Color3)
	local d = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(x, y),
		Size = UDim2.fromScale(w, h),
		BackgroundColor3 = color,
		BackgroundTransparency = 0,
		Parent = parent,
	})
	UIKit.corner(d, 0, 0.5)
	return d
end

function UIKit.paw(parent: Instance, size: number, color: Color3): Frame
	local holder = UIKit.frame({ Size = UDim2.fromOffset(size, size), Parent = parent })
	dot(holder, 0.5, 0.66, 0.44, 0.36, color)
	dot(holder, 0.22, 0.42, 0.19, 0.19, color)
	dot(holder, 0.4, 0.25, 0.19, 0.19, color)
	dot(holder, 0.6, 0.25, 0.19, 0.19, color)
	dot(holder, 0.78, 0.42, 0.19, 0.19, color)
	return holder
end

function UIKit.cross(parent: Instance, size: number, color: Color3): Frame
	local holder = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(size, size),
		Parent = parent,
	})
	for _, angle in ipairs({ 45, -45 }) do
		local bar = UIKit.frame({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.new(1, 0, 0, math.max(3, size * 0.16)),
			Rotation = angle,
			BackgroundColor3 = color,
			BackgroundTransparency = 0,
			Parent = holder,
		})
		UIKit.corner(bar, 2)
	end
	return holder
end

function UIKit.trash(parent: Instance, size: number, color: Color3): Frame
	local holder = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(size, size),
		Parent = parent,
	})
	local lid = UIKit.frame({ Position = UDim2.fromScale(0.12, 0.16), Size = UDim2.fromScale(0.76, 0.12), BackgroundColor3 = color, BackgroundTransparency = 0, Parent = holder })
	UIKit.corner(lid, 2)
	local handle = UIKit.frame({ Position = UDim2.fromScale(0.37, 0.04), Size = UDim2.fromScale(0.26, 0.12), BackgroundColor3 = color, BackgroundTransparency = 0, Parent = holder })
	UIKit.corner(handle, 2)
	local body = UIKit.frame({ Position = UDim2.fromScale(0.2, 0.33), Size = UDim2.fromScale(0.6, 0.62), BackgroundColor3 = color, BackgroundTransparency = 0, Parent = holder })
	UIKit.corner(body, 3)
	return holder
end

function UIKit.coin(parent: Instance, size: number): Frame
	local outer = UIKit.frame({ Size = UDim2.fromOffset(size, size), BackgroundColor3 = Color3.fromRGB(255, 194, 26), BackgroundTransparency = 0, Parent = parent })
	UIKit.corner(outer, 0, 0.5)
	local inner = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(0.58, 0.58),
		Parent = outer,
	})
	UIKit.corner(inner, 0, 0.5)
	UIKit.stroke(inner, Color3.fromRGB(183, 121, 31), math.max(1, size * 0.1))
	return outer
end

---------------------------------------------------------------------
-- Rarity colors on text
---------------------------------------------------------------------

function UIKit.applyRarity(label: TextLabel, rarityName: string)
	local old = label:FindFirstChild("RarityGradient")
	if old then
		old:Destroy()
	end
	local rarity = PetConfig.Rarities[rarityName]
	if not rarity then
		label.TextColor3 = UIKit.C.Muted
		return
	end
	if rarity.Gradient then
		label.TextColor3 = Color3.new(1, 1, 1)
		local keys = {}
		for i, color in ipairs(rarity.Gradient) do
			table.insert(keys, ColorSequenceKeypoint.new((i - 1) / math.max(1, #rarity.Gradient - 1), color))
		end
		UIKit.make("UIGradient", { Name = "RarityGradient", Color = ColorSequence.new(keys), Parent = label })
	else
		label.TextColor3 = rarity.Color
	end
end

function UIKit.rarityColor(rarityName: string): Color3
	local rarity = PetConfig.Rarities[rarityName]
	return if rarity then rarity.Color else UIKit.C.Muted
end

---------------------------------------------------------------------
-- 3D pictures (ViewportFrame)
---------------------------------------------------------------------

local views = setmetatable({}, { __mode = "k" })

function UIKit.viewport(props: { [string]: any }): ViewportFrame
	local p = table.clone(props)
	p.BackgroundTransparency = p.BackgroundTransparency or 1
	p.Ambient = p.Ambient or Color3.fromRGB(190, 195, 215)
	p.LightColor = p.LightColor or Color3.fromRGB(255, 255, 255)
	p.LightDirection = p.LightDirection or Vector3.new(-0.6, -1, -0.8)
	local vp = UIKit.make("ViewportFrame", p)
	local camera = UIKit.make("Camera", { FieldOfView = 30, Parent = vp })
	vp.CurrentCamera = camera
	return vp
end

-- Puts a model into the picture and frames it. yaw/pitch in degrees; 215 / 18 shows
-- the front and the right side from a bit above (the same view as the design canvas).
function UIKit.show(vp: ViewportFrame, model: Model?, yaw: number?, pitch: number?, fill: number?)
	for _, child in ipairs(vp:GetChildren()) do
		if child:IsA("Model") or child:IsA("BasePart") then
			child:Destroy()
		end
	end
	if not model then
		views[vp] = nil
		return
	end
	model.Parent = vp
	local cf, size = model:GetBoundingBox()
	local camera = vp.CurrentCamera :: Camera
	local radius = size.Magnitude / 2
	local distance = radius / math.tan(math.rad(camera.FieldOfView / 2)) * (fill or 0.9)
	views[vp] = { Center = cf.Position, Distance = distance, Pitch = pitch or 18 }
	UIKit.orbit(vp, yaw or 215)
end

function UIKit.orbit(vp: ViewportFrame, yaw: number)
	local view = views[vp]
	local camera = vp.CurrentCamera
	if not view or not camera then
		return
	end
	local y, p = math.rad(yaw), math.rad(view.Pitch)
	local direction = Vector3.new(-math.cos(p) * math.sin(y), math.sin(p), math.cos(p) * math.cos(y))
	camera.CFrame = CFrame.lookAt(view.Center + direction * view.Distance, view.Center)
end

---------------------------------------------------------------------
-- Screen-size scaling: designed for a phone held sideways, grows on bigger screens
---------------------------------------------------------------------

function UIKit.autoScale(object: GuiObject, screenGui: ScreenGui, designWidth: number, designHeight: number, minScale: number?, maxScale: number?): UIScale
	local scale = UIKit.make("UIScale", { Parent = object })
	local function update()
		local size = screenGui.AbsoluteSize
		if size.X < 1 or size.Y < 1 then
			return
		end
		local s = math.min(size.X / designWidth, size.Y / designHeight)
		scale.Scale = math.clamp(s, minScale or 0.55, maxScale or 1.5)
	end
	screenGui:GetPropertyChangedSignal("AbsoluteSize"):Connect(update)
	update()
	return scale
end

return UIKit
