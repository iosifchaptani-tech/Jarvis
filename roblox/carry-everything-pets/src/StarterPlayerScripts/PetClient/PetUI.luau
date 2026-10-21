--[[
	PetUI  (StarterPlayerScripts > PetClient > PetUI, a ModuleScript)

	All pet menus, built in code (nothing to place by hand):
	  - the orange PETS button on the left with the equipped count and the multiplier
	  - the Pets menu: every pet as a card (unfound pets are dark "?" cards), a turning
	    3D picture of the chosen pet, Equip / Unequip / Delete, Equip Best, Unequip All,
	    Formation (Arc / Circle / V) and Effects (High / Low / Off)
	  - the egg panel that opens at an egg: odds of every pet, Open 1, Open 3
	  - short messages at the top ("Not enough Coins", "X hatched a Mythic ...")
	Sized for a phone held sideways (buttons at least 44 px) and scaled up on bigger screens.
]]

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextChatService = game:GetService("TextChatService")

local Shared = ReplicatedStorage:WaitForChild("PetShared")
local PetConfig = require(Shared:WaitForChild("PetConfig"))
local PetBuilder = require(Shared:WaitForChild("PetBuilder"))
local PetLogic = require(Shared:WaitForChild("PetLogic"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local C = UIKit.C
local WHITE = Color3.new(1, 1, 1)
local SILHOUETTE = Color3.fromRGB(8, 10, 22)

local PetUI = {}

local player = Players.LocalPlayer
local remotes: any = nil
local Renderer: any = nil
local Cutscene: any = nil
local gui: ScreenGui = nil :: any
local data: any = nil
local selected = PetConfig.PetOrder[1]
local deleteArmed: string? = nil
local busy = false
local currentEgg: any = nil
local ui: any = { Cards = {}, EggTiles = {} }

---------------------------------------------------------------------
-- Talking to the server
---------------------------------------------------------------------

local function request(action: string, arg: any): (boolean, any)
	local ok, success, result = pcall(function()
		return remotes.Request:InvokeServer(action, arg)
	end)
	if not ok then
		return false, "Connection problem, please try again"
	end
	return success == true, result
end

local function escape(text: string): string
	text = string.gsub(text, "&", "&amp;")
	text = string.gsub(text, "<", "&lt;")
	text = string.gsub(text, ">", "&gt;")
	return text
end

---------------------------------------------------------------------
-- Messages at the top of the screen
---------------------------------------------------------------------

local function toast(text: string, color: Color3?)
	if not ui.Toasts then
		return
	end
	ui.ToastList = ui.ToastList or {}
	while #ui.ToastList >= 4 do
		local oldest = table.remove(ui.ToastList, 1)
		oldest:Destroy()
	end
	local item = UIKit.text({
		Text = text,
		RichText = true,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 36),
		BackgroundColor3 = C.Panel,
		BackgroundTransparency = 0.05,
		TextSize = 18,
		TextColor3 = color or C.Text,
		Parent = ui.Toasts,
	})
	UIKit.corner(item, 12)
	UIKit.make("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16), Parent = item })
	local stroke = UIKit.stroke(item, C.Border, 2)
	table.insert(ui.ToastList, item)
	task.delay(3, function()
		if not item.Parent then
			return
		end
		UIKit.tween(item, 0.35, { TextTransparency = 1, BackgroundTransparency = 1 })
		UIKit.tween(stroke, 0.35, { Transparency = 1 })
		task.wait(0.4)
		local index = table.find(ui.ToastList, item)
		if index then
			table.remove(ui.ToastList, index)
		end
		item:Destroy()
	end)
end

---------------------------------------------------------------------
-- Small lookups
---------------------------------------------------------------------

local function counts(petId: string): (number, number, boolean)
	if not data then
		return 0, 0, false
	end
	local owned = data.Counts[petId] or 0
	local equipped = data.Equipped[petId] or 0
	local known = owned > 0 or data.Discovered[petId] == true
	return owned, equipped, known
end

local function whereToFind(petId: string): string
	local found = {}
	for _, eggId in ipairs(PetConfig.EggOrder) do
		local egg = PetConfig.Eggs[eggId]
		for _, entry in ipairs(egg.Odds) do
			if entry[1] == petId then
				table.insert(found, egg.Name .. " " .. PetLogic.FormatPercent(entry[2]))
			end
		end
	end
	if #found == 0 then
		return "Game pass pet"
	end
	return "Found in " .. table.concat(found, ", ")
end

local function currencyValue(): any
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
		if value and (value:IsA("IntValue") or value:IsA("NumberValue")) then
			return value
		end
	end
	return nil
end

-- "You have 12,450 Coins" (from leaderstats, or from the server when coins live elsewhere)
local function balanceText(): string
	local value = currencyValue()
	local amount = if value then value.Value elseif data then data.Balance else nil
	if type(amount) ~= "number" then
		return ""
	end
	return ("You have %s %s"):format(PetLogic.FormatNumber(amount), PetConfig.CurrencyName)
end

---------------------------------------------------------------------
-- Refresh (called whenever the data changes)
---------------------------------------------------------------------

local function refreshDetail()
	local def = PetConfig.Pets[selected]
	if not def or not ui.DetailName then
		return
	end
	local owned, equipped, known = counts(selected)
	if ui.DetailPet ~= selected then
		ui.DetailPet = selected
		local pet = PetBuilder.Build(selected, { Fx = false, Scale = 1 })
		UIKit.show(ui.DetailViewport, pet.Model, 215, 18, 0.95)
	end
	ui.DetailViewport.ImageColor3 = if known then WHITE else SILHOUETTE
	ui.DetailName.Text = if known then def.Name else "???"
	ui.DetailRarity.Text = string.upper(def.Rarity) .. "  " .. PetLogic.FormatPower(def.Power)
	UIKit.applyRarity(ui.DetailRarity, def.Rarity)
	if owned > 0 then
		ui.DetailInfo.Text = ("Owned %d · Equipped %d"):format(owned, equipped)
	else
		ui.DetailInfo.Text = whereToFind(selected)
	end

	local rarity = PetConfig.Rarities[def.Rarity]
	local passFor = if def.Rarity == "Exclusive" then "CrystalKing" else nil
	local canBuy = owned == 0 and passFor ~= nil and (PetConfig.GamePasses[passFor] or 0) ~= 0
	ui.EquipButton.Visible = owned > 0 or canBuy
	ui.EquipButton.Text = if canBuy then "Get it" else "Equip"
	local free = data and data.EquippedTotal < data.MaxEquip
	ui.EquipButton.BackgroundColor3 = if canBuy or (equipped < owned and free) then C.GreenBright else C.Grey
	ui.UnequipButton.Visible = owned > 0
	ui.UnequipButton.BackgroundColor3 = if equipped > 0 then C.Blue else C.Grey
	ui.DeleteButton.Visible = owned > 0 and not (rarity and rarity.NoDelete)
	ui.DeleteButton.BackgroundColor3 = if deleteArmed == selected then C.RedBright else C.DarkRed
	ui.DeleteSure.Visible = deleteArmed == selected
	ui.DeleteIcon.Visible = deleteArmed ~= selected
end

local function refresh()
	if not data then
		return
	end
	local equippedText = ("%d/%d"):format(data.EquippedTotal, data.MaxEquip)
	local multiplierText = PetLogic.FormatMultiplier(data.Multiplier)
	ui.Badge.Text = equippedText
	ui.HudMultiplier.Text = multiplierText
	ui.EquippedChip.Text = "Equipped " .. equippedText
	ui.MultiplierChip.Text = multiplierText
	ui.Storage.Text = ("Storage %d/%d"):format(data.Storage, data.MaxStorage)
	ui.FormationButton.Text = "Formation: " .. tostring(data.Formation)
	ui.EffectsButton.Text = "Effects: " .. Renderer.GetFxSetting()

	for petId, card in pairs(ui.Cards) do
		local def = PetConfig.Pets[petId]
		local owned, equipped, known = counts(petId)
		card.Viewport.ImageColor3 = if known then WHITE else SILHOUETTE
		card.Viewport.ImageTransparency = if known and owned == 0 then 0.55 else 0
		card.Name.Text = if known then def.Name else "???"
		card.Name.TextColor3 = if known then C.Text else C.Unknown
		card.Question.Visible = not known
		card.Count.Visible = known and owned ~= 1
		card.Count.Text = "x" .. owned
		card.Equipped.Visible = equipped > 0
		card.Equipped.Text = if equipped > 1 then "E" .. equipped else "E"
		card.Bar.BackgroundColor3 = if known then UIKit.rarityColor(def.Rarity) else C.Unknown
		local isSelected = petId == selected
		card.Stroke.Color = if isSelected then WHITE else C.CardBorder
		card.Stroke.Thickness = if isSelected then 3 else 2
	end
	refreshDetail()

	if currentEgg and ui.EggBalance then
		ui.EggBalance.Text = balanceText()
	end
end

local function select(petId: string)
	if selected ~= petId then
		deleteArmed = nil
	end
	selected = petId
	refresh()
end

---------------------------------------------------------------------
-- Opening and closing
---------------------------------------------------------------------

local function closeInventory()
	if ui.Inventory and ui.Inventory.Visible then
		ui.Inventory.Visible = false
		deleteArmed = nil
	end
end

local function openInventory()
	if busy then
		return
	end
	if ui.EggPanel then
		ui.EggPanel.Visible = false
		currentEgg = nil
	end
	ui.Inventory.Position = UDim2.new(0.5, 0, 0.5, 26)
	ui.Inventory.Visible = true
	UIKit.tween(ui.Inventory, 0.22, { Position = UDim2.fromScale(0.5, 0.5) }, Enum.EasingStyle.Back)
	refresh()
end

local function toggleInventory()
	if ui.Inventory.Visible then
		closeInventory()
	else
		openInventory()
	end
end

local function closeEgg()
	currentEgg = nil
	if ui.EggPanel then
		ui.EggPanel.Visible = false
	end
end

---------------------------------------------------------------------
-- Actions
---------------------------------------------------------------------

local function act(action: string, arg: any)
	local ok, message = request(action, arg)
	if not ok then
		toast(tostring(message or "Something went wrong"), C.RedBright)
	end
	return ok
end

local function onEquip()
	local def = PetConfig.Pets[selected]
	local owned = counts(selected)
	if owned == 0 and def and def.Rarity == "Exclusive" then
		act("BuyPass", "CrystalKing")
		return
	end
	act("Equip", selected)
end

local function onDelete()
	if deleteArmed ~= selected then
		deleteArmed = selected
		refreshDetail()
		local armedFor = selected
		task.delay(2.5, function()
			if deleteArmed == armedFor then
				deleteArmed = nil
				refreshDetail()
			end
		end)
		return
	end
	deleteArmed = nil
	act("Delete", selected)
end

local function onFormation()
	local list = PetConfig.Formations
	local index = table.find(list, data and data.Formation or list[1]) or 1
	act("SetFormation", list[index % #list + 1])
end

local function onEffects()
	local order = { "High", "Low", "Off" }
	local index = table.find(order, Renderer.GetFxSetting()) or 1
	Renderer.SetFxSetting(order[index % #order + 1])
	refresh()
end

local function hatch(count: number)
	if busy or not currentEgg then
		return
	end
	if count == 3 and data and not data.TripleHatch then
		act("BuyPass", "TripleHatch")
		return
	end
	busy = true
	local eggId = currentEgg.Id
	local ok, result = request(if count == 3 then "Hatch3" else "Hatch", eggId)
	if not ok then
		busy = false
		toast(tostring(result), C.RedBright)
		return
	end
	ui.EggPanel.Visible = false
	closeInventory()
	local played = pcall(Cutscene.Play, eggId, result.Results, gui.Parent)
	if not played then
		local leftover = gui.Parent and gui.Parent:FindFirstChild("PetHatch")
		if leftover then
			leftover:Destroy()
		end
		for _, r in ipairs(result.Results) do
			toast("You got " .. PetConfig.Pets[r.Pet].Name .. "!")
		end
	end
	busy = false
	if currentEgg then
		ui.EggPanel.Visible = true
		refresh()
	end
end

---------------------------------------------------------------------
-- Building the screens
---------------------------------------------------------------------

local function buildToasts()
	local holder = UIKit.frame({
		Name = "Toasts",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 8),
		Size = UDim2.fromOffset(700, 200),
		Parent = gui,
	})
	UIKit.make("UIListLayout", {
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		Padding = UDim.new(0, 6),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = holder,
	})
	UIKit.autoScale(holder, gui, 844, 354, 0.75, 1.3)
	ui.Toasts = holder
end

local function buildHud()
	local hud = UIKit.frame({
		Name = "Hud",
		AnchorPoint = PetConfig.PetsButtonAnchor,
		Position = PetConfig.PetsButtonPosition,
		Size = UDim2.fromOffset(84, 108),
		Parent = gui,
	})
	UIKit.autoScale(hud, gui, 844, 354, 0.85, 1.35)
	local button = UIKit.button({
		Name = "PetsButton",
		Position = UDim2.fromOffset(8, 0),
		Size = UDim2.fromOffset(68, 68),
		BackgroundColor3 = C.Orange,
		Text = "",
		Radius = 18,
		Parent = hud,
	}, toggleInventory)
	UIKit.stroke(button, WHITE, 3)
	local paw = UIKit.paw(button, 30, WHITE)
	paw.AnchorPoint = Vector2.new(0.5, 0)
	paw.Position = UDim2.new(0.5, 0, 0, 7)
	UIKit.text({ Text = "PETS", Position = UDim2.fromOffset(0, 42), Size = UDim2.new(1, 0, 0, 18), TextSize = 15, Parent = button })
	local badge = UIKit.text({
		Name = "Badge",
		Text = "0/" .. PetConfig.MaxEquipped,
		Position = UDim2.new(1, -28, 0, -9),
		Size = UDim2.fromOffset(42, 20),
		BackgroundColor3 = C.GreenBright,
		BackgroundTransparency = 0,
		TextSize = 13,
		Parent = button,
	})
	UIKit.corner(badge, 0, 0.5)
	UIKit.stroke(badge, WHITE, 2)
	local multiplier = UIKit.text({
		Name = "Multiplier",
		Text = "x1",
		Position = UDim2.fromOffset(0, 78),
		Size = UDim2.fromOffset(84, 26),
		BackgroundColor3 = C.Panel,
		BackgroundTransparency = 0,
		TextColor3 = C.Gold,
		TextSize = 16,
		Parent = hud,
	})
	UIKit.corner(multiplier, 0, 0.5)
	UIKit.stroke(multiplier, Color3.fromRGB(255, 194, 26), 2)
	ui.Badge = badge
	ui.HudMultiplier = multiplier
end

local function chip(parent: Instance, text: string, x: number, width: number, gold: boolean?): TextLabel
	local label = UIKit.text({
		Text = text,
		Position = UDim2.fromOffset(x, 17),
		Size = UDim2.fromOffset(width, 30),
		BackgroundColor3 = if gold then C.GoldDark else C.Chip,
		BackgroundTransparency = 0,
		TextColor3 = if gold then C.Gold else C.Text,
		TextSize = 15,
		Parent = parent,
	})
	UIKit.corner(label, 0, 0.5)
	if gold then
		UIKit.stroke(label, Color3.fromRGB(255, 194, 26), 1)
	end
	return label
end

local function makeCard(petId: string, order: number)
	local def = PetConfig.Pets[petId]
	local card = UIKit.button({
		Name = petId,
		LayoutOrder = order,
		Text = "",
		BackgroundColor3 = C.Panel2,
		Radius = 14,
		Parent = ui.Grid,
	}, function()
		select(petId)
	end)
	local stroke = UIKit.stroke(card, C.CardBorder, 2)
	local viewport = UIKit.viewport({ Position = UDim2.fromOffset(4, 3), Size = UDim2.fromOffset(74, 62), Parent = card })
	UIKit.show(viewport, PetBuilder.Build(petId, { Fx = false, Scale = 1 }).Model, 215, 18, 0.82)
	local name = UIKit.text({
		Text = def.Name,
		Position = UDim2.fromOffset(3, 65),
		Size = UDim2.fromOffset(76, 22),
		TextSize = 12,
		TextScaled = true,
		TextWrapped = true,
		Parent = card,
	})
	UIKit.make("UITextSizeConstraint", { MaxTextSize = 12, MinTextSize = 8, Parent = name })
	local question = UIKit.text({
		Text = "?",
		Position = UDim2.fromOffset(0, 6),
		Size = UDim2.fromOffset(82, 56),
		TextSize = 40,
		TextColor3 = C.Unknown,
		Visible = false,
		Parent = card,
	})
	local count = UIKit.text({
		Text = "x1",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -4, 0, 4),
		Size = UDim2.fromOffset(30, 18),
		BackgroundColor3 = Color3.new(0, 0, 0),
		BackgroundTransparency = 0.3,
		TextSize = 12,
		Visible = false,
		Parent = card,
	})
	UIKit.corner(count, 0, 0.5)
	local equipped = UIKit.text({
		Text = "E",
		Position = UDim2.fromOffset(4, 4),
		Size = UDim2.fromOffset(26, 18),
		BackgroundColor3 = C.GreenBright,
		BackgroundTransparency = 0,
		TextSize = 12,
		Visible = false,
		Parent = card,
	})
	UIKit.corner(equipped, 0, 0.5)
	local bar = UIKit.frame({
		Position = UDim2.fromOffset(12, 90),
		Size = UDim2.fromOffset(58, 5),
		BackgroundColor3 = UIKit.rarityColor(def.Rarity),
		Parent = card,
	})
	UIKit.corner(bar, 0, 0.5)
	ui.Cards[petId] = {
		Stroke = stroke,
		Viewport = viewport,
		Name = name,
		Question = question,
		Count = count,
		Equipped = equipped,
		Bar = bar,
	}
end

local function buildInventory()
	local W = 692
	local holder = UIKit.frame({
		Name = "Inventory",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(W, 342),
		BackgroundColor3 = C.Panel,
		Visible = false,
		Parent = gui,
	})
	UIKit.corner(holder, 22)
	UIKit.stroke(holder, C.Border, 3)
	UIKit.autoScale(holder, gui, 884, 362, 0.5, 1.45)
	ui.Inventory = holder

	-- header
	UIKit.text({ Text = "PETS", Position = UDim2.fromOffset(16, 10), Size = UDim2.fromOffset(76, 44), TextSize = 26, TextXAlignment = Enum.TextXAlignment.Left, Parent = holder })
	ui.EquippedChip = chip(holder, "Equipped 0/4", 92, 132)
	ui.MultiplierChip = chip(holder, "x1", 232, 96, true)
	ui.Storage = UIKit.text({
		Text = "Storage 0/50",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromOffset(W - 70, 10),
		Size = UDim2.fromOffset(170, 44),
		Font = UIKit.BodyFont,
		TextSize = 14,
		TextColor3 = C.Muted,
		TextXAlignment = Enum.TextXAlignment.Right,
		Parent = holder,
	})
	local close = UIKit.button({ Name = "Close", Position = UDim2.fromOffset(W - 58, 10), Size = UDim2.fromOffset(44, 44), BackgroundColor3 = C.RedBright, Text = "", Parent = holder }, closeInventory)
	UIKit.cross(close, 20, WHITE)

	-- cards
	local grid = UIKit.make("ScrollingFrame", {
		Name = "Cards",
		Position = UDim2.fromOffset(14, 62),
		Size = UDim2.fromOffset(452, 212),
		BackgroundTransparency = 1,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Border,
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		CanvasSize = UDim2.new(),
		ScrollingDirection = Enum.ScrollingDirection.Y,
		Parent = holder,
	})
	UIKit.make("UIGridLayout", {
		CellSize = UDim2.fromOffset(82, 101),
		CellPadding = UDim2.fromOffset(8, 8),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = grid,
	})
	UIKit.make("UIPadding", { PaddingTop = UDim.new(0, 2), PaddingLeft = UDim.new(0, 2), Parent = grid })
	ui.Grid = grid
	for i, petId in ipairs(PetConfig.PetOrder) do
		makeCard(petId, i)
	end

	-- details of the chosen pet
	local detail = UIKit.frame({ Name = "Detail", Position = UDim2.fromOffset(474, 62), Size = UDim2.fromOffset(204, 212), BackgroundColor3 = C.Panel2, Parent = holder })
	UIKit.corner(detail, 16)
	ui.DetailViewport = UIKit.viewport({ Position = UDim2.fromOffset(8, 4), Size = UDim2.fromOffset(188, 92), Parent = detail })
	ui.DetailName = UIKit.text({ Text = "", Position = UDim2.fromOffset(10, 96), Size = UDim2.fromOffset(186, 24), TextSize = 20, TextXAlignment = Enum.TextXAlignment.Left, TextScaled = true, Parent = detail })
	UIKit.make("UITextSizeConstraint", { MaxTextSize = 20, Parent = ui.DetailName })
	ui.DetailRarity = UIKit.text({ Text = "", Position = UDim2.fromOffset(10, 120), Size = UDim2.fromOffset(186, 16), TextSize = 14, TextXAlignment = Enum.TextXAlignment.Left, Parent = detail })
	ui.DetailInfo = UIKit.text({
		Text = "",
		Position = UDim2.fromOffset(10, 137),
		Size = UDim2.fromOffset(186, 18),
		Font = UIKit.BodyFont,
		TextSize = 12,
		TextColor3 = C.Muted,
		TextXAlignment = Enum.TextXAlignment.Left,
		TextScaled = true,
		Parent = detail,
	})
	UIKit.make("UITextSizeConstraint", { MaxTextSize = 12, MinTextSize = 8, Parent = ui.DetailInfo })
	ui.EquipButton = UIKit.button({ Position = UDim2.fromOffset(8, 160), Size = UDim2.fromOffset(70, 44), BackgroundColor3 = C.GreenBright, Text = "Equip", TextSize = 16, Parent = detail }, onEquip)
	ui.UnequipButton = UIKit.button({ Position = UDim2.fromOffset(82, 160), Size = UDim2.fromOffset(70, 44), BackgroundColor3 = C.Grey, Text = "Unequip", TextSize = 15, Parent = detail }, function()
		act("Unequip", selected)
	end)
	ui.DeleteButton = UIKit.button({ Position = UDim2.fromOffset(156, 160), Size = UDim2.fromOffset(44, 44), BackgroundColor3 = C.DarkRed, Text = "", Parent = detail }, onDelete)
	ui.DeleteIcon = UIKit.trash(ui.DeleteButton, 20, WHITE)
	ui.DeleteSure = UIKit.text({ Text = "Sure?", Size = UDim2.fromScale(1, 1), TextSize = 13, Visible = false, Parent = ui.DeleteButton })

	-- bottom bar
	local y = 284
	UIKit.button({ Position = UDim2.fromOffset(14, y), Size = UDim2.fromOffset(162, 46), BackgroundColor3 = C.Green, Text = "Equip Best", Parent = holder }, function()
		act("EquipBest")
	end)
	UIKit.button({ Position = UDim2.fromOffset(182, y), Size = UDim2.fromOffset(162, 46), BackgroundColor3 = C.Red, Text = "Unequip All", Parent = holder }, function()
		act("UnequipAll")
	end)
	ui.FormationButton = UIKit.button({ Position = UDim2.fromOffset(350, y), Size = UDim2.fromOffset(162, 46), BackgroundColor3 = C.Chip, Text = "Formation: Arc", TextSize = 16, Parent = holder }, onFormation)
	UIKit.stroke(ui.FormationButton, C.Border, 2)
	ui.EffectsButton = UIKit.button({ Position = UDim2.fromOffset(518, y), Size = UDim2.fromOffset(160, 46), BackgroundColor3 = C.Chip, Text = "Effects: High", TextSize = 16, Parent = holder }, onEffects)
	UIKit.stroke(ui.EffectsButton, C.Border, 2)
end

local function buildEggTiles(eggId: string): Frame
	local egg = PetConfig.Eggs[eggId]
	local row = UIKit.frame({ Name = eggId, Position = UDim2.fromOffset(14, 56), Size = UDim2.fromOffset(552, 100), Visible = false, Parent = ui.EggPanel })
	UIKit.make("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		Padding = UDim.new(0, 8),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = row,
	})
	local n = #egg.Odds
	local width = math.floor((552 - 8 * (n - 1)) / n)
	for i, entry in ipairs(egg.Odds) do
		local petId, chance = entry[1], entry[2]
		local def = PetConfig.Pets[petId]
		local tile = UIKit.frame({ LayoutOrder = i, Size = UDim2.fromOffset(width, 100), BackgroundColor3 = C.Panel2, Parent = row })
		UIKit.corner(tile, 14)
		local vp = UIKit.viewport({ Position = UDim2.fromOffset(4, 2), Size = UDim2.new(1, -8, 0, 58), Parent = tile })
		UIKit.show(vp, PetBuilder.Build(petId, { Fx = false, Scale = 1 }).Model, 215, 18, 0.85)
		local name = UIKit.text({ Text = def.Name, Position = UDim2.fromOffset(2, 60), Size = UDim2.new(1, -4, 0, 16), TextSize = 12, TextScaled = true, Parent = tile })
		UIKit.make("UITextSizeConstraint", { MaxTextSize = 12, MinTextSize = 8, Parent = name })
		local percent = UIKit.text({ Text = PetLogic.FormatPercent(chance), Position = UDim2.fromOffset(0, 76), Size = UDim2.new(1, 0, 0, 18), TextSize = 16, Parent = tile })
		UIKit.applyRarity(percent, def.Rarity)
		local bar = UIKit.frame({ Position = UDim2.new(0, 10, 1, -5), Size = UDim2.new(1, -20, 0, 4), BackgroundColor3 = UIKit.rarityColor(def.Rarity), Parent = tile })
		UIKit.corner(bar, 0, 0.5)
	end
	ui.EggTiles[eggId] = row
	return row
end

local function buildEggPanel()
	local W = 580
	local holder = UIKit.frame({
		Name = "EggPanel",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -10),
		Size = UDim2.fromOffset(W, 222),
		BackgroundColor3 = C.Panel,
		Visible = false,
		Parent = gui,
	})
	UIKit.corner(holder, 22)
	ui.EggStroke = UIKit.stroke(holder, C.Orange, 3)
	UIKit.autoScale(holder, gui, 640, 420, 0.55, 1.3)
	ui.EggPanel = holder

	local header = UIKit.frame({ Position = UDim2.fromOffset(16, 8), Size = UDim2.fromOffset(330, 44), Parent = holder })
	UIKit.make("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal,
		VerticalAlignment = Enum.VerticalAlignment.Center,
		Padding = UDim.new(0, 10),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = header,
	})
	ui.EggName = UIKit.text({ LayoutOrder = 1, Text = "Egg", AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 40), TextSize = 26, Parent = header })
	local coin = UIKit.coin(header, 20)
	coin.LayoutOrder = 2
	ui.EggPrice = UIKit.text({ LayoutOrder = 3, Text = "0", AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 40), TextSize = 19, TextColor3 = C.Gold, Parent = header })
	ui.EggBalance = UIKit.text({
		Text = "",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromOffset(W - 70, 8),
		Size = UDim2.fromOffset(200, 44),
		Font = UIKit.BodyFont,
		TextSize = 13,
		TextColor3 = C.Muted,
		TextXAlignment = Enum.TextXAlignment.Right,
		Parent = holder,
	})
	local close = UIKit.button({ Position = UDim2.fromOffset(W - 58, 8), Size = UDim2.fromOffset(44, 44), BackgroundColor3 = C.RedBright, Text = "", Parent = holder }, closeEgg)
	UIKit.cross(close, 20, WHITE)

	ui.OpenOne = UIKit.button({ Position = UDim2.fromOffset(14, 164), Size = UDim2.fromOffset(272, 48), BackgroundColor3 = C.Green, Text = "Open 1", TextSize = 20, Parent = holder }, function()
		hatch(1)
	end)
	ui.OpenThree = UIKit.button({ Position = UDim2.fromOffset(294, 164), Size = UDim2.fromOffset(272, 48), BackgroundColor3 = C.Blue, Text = "Open 3", TextSize = 20, Parent = holder }, function()
		hatch(3)
	end)
end

local function openEgg(eggId: string, prompt: ProximityPrompt)
	local egg = PetConfig.Eggs[eggId]
	if not egg or busy then
		return
	end
	closeInventory()
	currentEgg = { Id = eggId, Part = prompt.Parent }
	ui.EggName.Text = egg.Name
	ui.EggPrice.Text = PetLogic.Commas(egg.Price)
	ui.EggStroke.Color = egg.Colors.Spots[1]
	for id, row in pairs(ui.EggTiles) do
		row.Visible = false
	end
	local row = ui.EggTiles[eggId] or buildEggTiles(eggId)
	row.Visible = true
	ui.OpenOne.Text = "Open 1 · " .. PetLogic.FormatNumber(egg.Price)
	if data and not data.TripleHatch then
		ui.OpenThree.Text = "Open 3 · Game Pass"
	else
		ui.OpenThree.Text = "Open 3 · " .. PetLogic.FormatNumber(egg.Price * 3)
	end
	ui.EggPanel.Position = UDim2.new(0.5, 0, 1, 30)
	ui.EggPanel.Visible = true
	UIKit.tween(ui.EggPanel, 0.22, { Position = UDim2.new(0.5, 0, 1, -10) }, Enum.EasingStyle.Back)
	refresh()
end

local function onAnnounce(payload: any)
	if type(payload) ~= "table" then
		return
	end
	local def = PetConfig.Pets[payload.Pet]
	if not def then
		return
	end
	local color = UIKit.rarityColor(def.Rarity):ToHex()
	local text = ('%s hatched a <font color="#%s">%s %s</font>!'):format(escape(tostring(payload.Name)), color, def.Rarity, def.Name)
	toast(text)
	pcall(function()
		local channels = TextChatService:FindFirstChild("TextChannels")
		local general = channels and channels:FindFirstChild("RBXGeneral")
		if general and general:IsA("TextChannel") then
			general:DisplaySystemMessage(text)
		end
	end)
end

---------------------------------------------------------------------
-- Start
---------------------------------------------------------------------

function PetUI.Start(deps: { Renderer: any, Cutscene: any })
	Renderer = deps.Renderer
	Cutscene = deps.Cutscene
	local folder = ReplicatedStorage:WaitForChild("PetRemotes")
	remotes = {
		Request = folder:WaitForChild("PetRequest"),
		Update = folder:WaitForChild("PetUpdate"),
	}

	gui = UIKit.make("ScreenGui", {
		Name = "PetUI",
		ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		DisplayOrder = 5,
		Parent = player:WaitForChild("PlayerGui"),
	})
	pcall(function()
		(gui :: any).ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
	end)

	buildToasts()
	buildHud()
	buildInventory()
	buildEggPanel()

	remotes.Update.OnClientEvent:Connect(function(kind: string, payload: any)
		if kind == "Data" then
			data = payload
			refresh()
		elseif kind == "Toast" then
			toast(tostring(payload))
		elseif kind == "Announce" then
			onAnnounce(payload)
		end
	end)

	ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt)
		if prompt.Name == "PetEggPrompt" then
			local eggId = prompt:GetAttribute("EggId")
			if type(eggId) == "string" then
				openEgg(eggId, prompt)
			end
		end
	end)

	Renderer.FxChanged.Event:Connect(refresh)

	-- the chosen pet slowly turns while the menu is open
	RunService.RenderStepped:Connect(function()
		if ui.Inventory.Visible then
			UIKit.orbit(ui.DetailViewport, 215 + os.clock() * 40)
		end
	end)

	-- close the egg panel when walking away; keep the coin count fresh
	task.spawn(function()
		while true do
			task.wait(0.3)
			if currentEgg then
				local character = player.Character
				local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
				local part = currentEgg.Part
				if not rootPart or not part or not part:IsA("BasePart") or (rootPart.Position - part.Position).Magnitude > PetConfig.EggRange + 3 then
					closeEgg()
				else
					ui.EggBalance.Text = balanceText()
				end
			end
		end
	end)

	-- first data (the server also sends it by itself when it is ready)
	task.spawn(function()
		for _ = 1, 30 do
			if data then
				return
			end
			local ok = request("GetData")
			if ok then
				return
			end
			task.wait(2)
		end
	end)
end

return PetUI
