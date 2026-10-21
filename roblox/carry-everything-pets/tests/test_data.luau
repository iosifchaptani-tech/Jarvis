--!nocheck
-- Checks PetConfig and PetModels for mistakes (missing pets, odds that don't add up,
-- broken model lines, effects pointing at parts that don't exist ...).
-- Run: python tools/run_tests.py   (PRESET_NAMES is filled in from PetBuilder by the runner)

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

local PetConfig = require(shared:FindFirstChild("PetConfig"))
local PetModels = require(shared:FindFirstChild("PetModels"))
local PetLogic = require(shared:FindFirstChild("PetLogic"))

local function keys(t)
	local out = {}
	for k in pairs(t) do
		table.insert(out, k)
	end
	table.sort(out)
	return table.concat(out, ",")
end

test("the same 10 pets everywhere", function()
	local order = table.clone(PetConfig.PetOrder)
	table.sort(order)
	assert(#order == 10, "PetOrder should list 10 pets")
	assert(table.concat(order, ",") == keys(PetConfig.Pets), "PetOrder and Pets differ")
	assert(keys(PetModels) == keys(PetConfig.Pets), "PetModels and Pets differ")
end)

test("rarities exist and power grows with rarity", function()
	local lastPower = -1
	for _, petId in ipairs(PetConfig.PetOrder) do
		local def = PetConfig.Pets[petId]
		local rarity = PetConfig.Rarities[def.Rarity]
		assert(rarity, petId .. " has unknown rarity " .. tostring(def.Rarity))
		assert(def.Power > lastPower, petId .. " should be stronger than the pet before it")
		lastPower = def.Power
		assert(type(def.Name) == "string" and #def.Name > 0, petId .. " needs a Name")
	end
end)

test("eggs: odds add up to 100 and only name real pets", function()
	local order = table.clone(PetConfig.EggOrder)
	table.sort(order)
	assert(table.concat(order, ",") == keys(PetConfig.Eggs), "EggOrder and Eggs differ")
	for eggId, egg in pairs(PetConfig.Eggs) do
		local total = PetLogic.OddsTotal(egg.Odds)
		assert(math.abs(total - 100) < 1e-9, eggId .. " odds add up to " .. total)
		assert(egg.Price > 0, eggId .. " needs a price")
		for _, entry in ipairs(egg.Odds) do
			local def = PetConfig.Pets[entry[1]]
			assert(def, eggId .. " names unknown pet " .. tostring(entry[1]))
			assert(def.Rarity ~= "Exclusive", eggId .. " must not contain the Exclusive pet")
		end
	end
end)

local VALID_MAT = { P = true, N = true, G = true, I = true }
local VALID_SHAPE = { B = true, W = true }
local VALID_GROUP = { ["-"] = true, Head = true, Tail = true, WingL = true, WingR = true }

for _, petId in ipairs(PetConfig.PetOrder) do
	test(petId .. " model lines are valid", function()
		local source = PetModels[petId]
		local lineCount = 0
		for line in string.gmatch(source.Parts, "[^\n]+") do
			if string.match(line, "%S") then
				lineCount += 1
				local tokens = {}
				for tok in string.gmatch(line, "%S+") do
					table.insert(tokens, tok)
				end
				assert(#tokens >= 14, petId .. ": short line: " .. line)
			end
		end
		local parts = PetLogic.ParseModel(source.Parts)
		assert(#parts >= lineCount, petId .. ": a line was not read")
		assert(#parts >= 15 and #parts <= 40, petId .. " has " .. #parts .. " parts (keep 15-40)")
		local pivots = PetLogic.ExpandPivots(source.Pivots)
		local names = {}
		for _, p in ipairs(parts) do
			assert(not names[p.Name], petId .. ": two parts are called " .. p.Name)
			names[p.Name] = true
			assert(string.match(p.Color, "^%x%x%x%x%x%x$"), petId .. ": bad color on " .. p.Name)
			assert(VALID_MAT[p.Mat], petId .. ": bad material on " .. p.Name)
			assert(VALID_SHAPE[p.Shape], petId .. ": bad shape on " .. p.Name)
			assert(VALID_GROUP[p.Group], petId .. ": bad group on " .. p.Name)
			if p.Group ~= "-" then
				assert(pivots[p.Group], petId .. ": no pivot for group " .. p.Group)
			end
			for axis = 1, 3 do
				assert(p.Size[axis] > 0 and p.Size[axis] <= 3, petId .. ": odd size on " .. p.Name)
				assert(math.abs(p.Pos[axis]) <= 4.5, petId .. ": " .. p.Name .. " is too far from the middle")
			end
		end
		assert(source.WingAxis == "Z" or source.WingAxis == "Y", petId .. ": WingAxis must be Z or Y")
		local wings = pivots.WingL ~= nil
		local hasWingParts = false
		for _, p in ipairs(parts) do
			if p.Group == "WingL" then
				hasWingParts = true
			end
		end
		assert(wings == hasWingParts, petId .. ": wing pivot and wing parts don't match")
	end)

	test(petId .. " aura points at things that exist", function()
		local def = PetConfig.Pets[petId]
		local aura = def.Aura
		assert(aura and aura.Outline, petId .. " needs an Outline")
		assert(aura.Rings and #aura.Rings >= 1, petId .. " needs at least one ring")
		local parts = PetLogic.ParseModel(PetModels[petId].Parts)
		local names = {}
		for _, p in ipairs(parts) do
			names[p.Name] = true
		end
		for _, ring in ipairs(aura.Rings) do
			assert(ring.Radius > 0 and ring.Width > 0, petId .. " ring needs Radius and Width")
			assert(ring.Colors == "Rainbow" or (type(ring.Colors) == "table" and ring.Colors[2]), petId .. " ring needs 2 colors")
		end
		for _, spec in ipairs(aura.Particles or {}) do
			assert(table.find(PRESET_NAMES, spec.Preset), petId .. ": unknown particle preset " .. tostring(spec.Preset))
			assert(spec.Rate and spec.Rate > 0 and spec.Rate <= 30, petId .. ": keep particle Rate between 1 and 30")
			local where = spec.Where or "Body"
			if string.sub(where, 1, 5) == "Part:" then
				assert(names[string.sub(where, 6)], petId .. ": no part " .. where)
			elseif string.sub(where, 1, 6) == "Parts:" then
				for name in string.gmatch(string.sub(where, 7), "[^,%s]+") do
					assert(names[name], petId .. ": no part " .. name)
				end
			else
				assert(where == "Body" or where == "Ground", petId .. ": bad Where " .. where)
			end
		end
		if aura.Trails then
			for _, name in ipairs(aura.Trails.Parts) do
				assert(names[name], petId .. ": trail on missing part " .. name)
			end
		end
		local rarity = PetConfig.Rarities[def.Rarity]
		if rarity.Order >= 4 then
			assert(aura.Shell, petId .. ": Legendary and up should have an aura shell")
			assert(#aura.Rings >= 3, petId .. ": Legendary and up should have 3+ rings")
		end
	end)
end

test("formations and limits make sense", function()
	assert(table.find(PetConfig.Formations, PetConfig.DefaultFormation), "DefaultFormation must be in Formations")
	assert(PetConfig.MaxEquipped >= 1 and PetConfig.MaxEquipped <= 12, "MaxEquipped 1-12")
	assert(PetConfig.MaxStorage >= PetConfig.MaxEquipped, "MaxStorage too small")
	assert(PetConfig.Fx.OutlineBudget <= 31, "Roblox shows at most 31 outlines")
end)

print_real(("%d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("tests failed")
end
