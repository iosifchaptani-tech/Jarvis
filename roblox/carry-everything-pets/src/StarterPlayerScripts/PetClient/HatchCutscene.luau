--[[
	HatchCutscene  (StarterPlayerScripts > PetClient > HatchCutscene, a ModuleScript)

	The egg opening: the egg pops up, shakes three times (harder each time),
	a white flash, then each new pet appears in front of spinning light rays in its
	rarity color with its name, rarity, power and a "NEW!" tag for first finds.
	Tap anywhere (or wait a few seconds) to continue. Works for 1 or 3 eggs.
]]

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))
local PetBuilder = require(Shared:WaitForChild("PetBuilder"))
local PetLogic = require(Shared:WaitForChild("PetLogic"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local HatchCutscene = {}

local STAGE_W, STAGE_H = 780, 380

local function rays(parent: Instance, rarityName: string): Frame
	local holder = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(120, 110),
		Size = UDim2.fromOffset(320, 320),
		Parent = parent,
	})
	local rarity = PetConfig.Rarities[rarityName]
	local base = if rarity then rarity.Color else Color3.new(1, 1, 1)
	local gradient = rarity and rarity.Gradient
	for i = 0, 11 do
		local color = base
		if gradient then
			color = gradient[(i % #gradient) + 1]
		end
		local bar = UIKit.frame({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.new(0, 22, 1, 0),
			Rotation = i * 15,
			BackgroundColor3 = color,
			BackgroundTransparency = 0.35,
			Parent = holder,
		})
		UIKit.make("UIGradient", {
			Rotation = 90,
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.5, 0.2),
				NumberSequenceKeypoint.new(1, 1),
			}),
			Parent = bar,
		})
	end
	local glow = UIKit.frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(170, 170),
		BackgroundColor3 = base,
		BackgroundTransparency = 0.7,
		Parent = holder,
	})
	UIKit.corner(glow, 0, 0.5)
	return holder
end

-- Plays the animation and returns when the player taps (or after a few seconds).
function HatchCutscene.Play(eggId: string, results: { any }, playerGui: Instance)
	local connection: RBXScriptConnection? = nil
	local gui = UIKit.make("ScreenGui", {
		Name = "PetHatch",
		ResetOnSpawn = false,
		IgnoreGuiInset = true,
		DisplayOrder = 50,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		Parent = playerGui,
	})
	local ok, err = pcall(function()
		local dim = UIKit.frame({ Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.fromRGB(6, 4, 14), BackgroundTransparency = 1, Parent = gui })
		UIKit.tween(dim, 0.25, { BackgroundTransparency = 0.12 })

		local stage = UIKit.frame({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.fromOffset(STAGE_W, STAGE_H),
			Parent = gui,
		})
		UIKit.autoScale(stage, gui, STAGE_W + 40, STAGE_H + 20, 0.45, 1.5)

		-- 1. the egg pops up and shakes
		local eggView = UIKit.viewport({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(STAGE_W / 2, STAGE_H / 2 - 10),
			Size = UDim2.fromOffset(10, 10),
			Parent = stage,
		})
		UIKit.show(eggView, PetBuilder.BuildEgg(eggId, 1), 200, 10, 0.8)
		UIKit.tween(eggView, 0.35, { Size = UDim2.fromOffset(250, 250) }, Enum.EasingStyle.Back)
		task.wait(0.45)
		local center = eggView.Position
		for round = 1, 3 do
			local amount = 5 * round
			for _ = 1, 2 do
				eggView.Position = center + UDim2.fromOffset(amount, 0)
				UIKit.orbit(eggView, 200 + amount * 1.5)
				task.wait(0.05)
				eggView.Position = center + UDim2.fromOffset(-amount, 0)
				UIKit.orbit(eggView, 200 - amount * 1.5)
				task.wait(0.05)
			end
			eggView.Position = center
			UIKit.orbit(eggView, 200)
			task.wait(0.22)
		end

		-- 2. flash
		local flash = UIKit.frame({ Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0, ZIndex = 20, Parent = gui })
		eggView:Destroy()
		UIKit.tween(flash, 0.45, { BackgroundTransparency = 1 })

		-- 3. the pets
		local count = #results
		local slotW = 240
		local gap = 20
		local startX = (STAGE_W - (count * slotW + (count - 1) * gap)) / 2
		local spinning = {}
		local rayFrames = {}
		if count == 1 then
			UIKit.text({ Text = "YOU HATCHED", Position = UDim2.fromOffset(0, -6), Size = UDim2.fromOffset(STAGE_W, 28), TextSize = 22, TextColor3 = Color3.fromRGB(255, 220, 230), Parent = stage })
		end
		for i, result in ipairs(results) do
			local def = PetConfig.Pets[result.Pet]
			if def then
				local slot = UIKit.frame({ Position = UDim2.fromOffset(startX + (i - 1) * (slotW + gap), 24), Size = UDim2.fromOffset(slotW, 340), Parent = stage })
				local pop = UIKit.make("UIScale", { Scale = 0, Parent = slot })
				table.insert(rayFrames, rays(slot, def.Rarity))
				local view = UIKit.viewport({ AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(120, 110), Size = UDim2.fromOffset(220, 220), Parent = slot })
				UIKit.show(view, PetBuilder.Build(result.Pet, { Fx = false, Scale = 1 }).Model, 215, 16, 0.9)
				table.insert(spinning, view)
				UIKit.text({ Text = def.Name, Position = UDim2.fromOffset(0, 226), Size = UDim2.fromOffset(slotW, 36), TextSize = 30, TextScaled = true, Parent = slot })
				local rarityLabel = UIKit.text({
					Text = string.upper(def.Rarity) .. "  " .. PetLogic.FormatPower(def.Power) .. " POWER",
					Position = UDim2.fromOffset(0, 262),
					Size = UDim2.fromOffset(slotW, 22),
					TextSize = 18,
					Parent = slot,
				})
				UIKit.applyRarity(rarityLabel, def.Rarity)
				if result.New then
					local tag = UIKit.text({
						Text = "NEW!",
						Position = UDim2.fromOffset(slotW - 84, 14),
						Size = UDim2.fromOffset(70, 32),
						Rotation = 10,
						BackgroundColor3 = Color3.fromRGB(255, 225, 77),
						BackgroundTransparency = 0,
						TextColor3 = Color3.fromRGB(42, 26, 0),
						TextSize = 20,
						Parent = slot,
					})
					UIKit.corner(tag, 10)
					UIKit.stroke(tag, Color3.new(1, 1, 1), 3)
				end
				UIKit.tween(pop, 0.4, { Scale = 1 }, Enum.EasingStyle.Back)
				task.wait(0.12)
			end
		end
		UIKit.text({
			Text = "Tap anywhere to continue",
			Position = UDim2.fromOffset(0, STAGE_H - 4),
			Size = UDim2.fromOffset(STAGE_W, 22),
			Font = UIKit.BodyFont,
			TextSize = 15,
			TextColor3 = Color3.fromRGB(185, 176, 201),
			Parent = stage,
		})

		local yaw = 215
		connection = RunService.RenderStepped:Connect(function(dt)
			yaw += dt * 50
			for _, view in ipairs(spinning) do
				UIKit.orbit(view, yaw)
			end
			for _, frame in ipairs(rayFrames) do
				frame.Rotation += dt * 25
			end
		end)

		local done = false
		local catcher = UIKit.make("TextButton", {
			Size = UDim2.fromScale(1, 1),
			BackgroundTransparency = 1,
			Text = "",
			ZIndex = 30,
			Parent = gui,
		})
		catcher.Activated:Connect(function()
			done = true
		end)
		local began = os.clock()
		task.wait(0.4)
		while not done and os.clock() - began < 6.5 do
			task.wait(0.05)
		end

		UIKit.tween(dim, 0.25, { BackgroundTransparency = 1 })
		UIKit.tween(stage, 0.25, { Position = UDim2.new(0.5, 0, 0.5, 40) })
		task.wait(0.27)
	end)
	-- always clean up, even if something above went wrong
	if connection then
		connection:Disconnect()
	end
	gui:Destroy()
	if not ok then
		error(err, 0)
	end
end

return HatchCutscene
