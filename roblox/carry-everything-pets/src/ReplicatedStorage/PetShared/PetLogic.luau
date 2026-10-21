--[[
	PetLogic  (ReplicatedStorage > PetShared > PetLogic, a ModuleScript)

	Plain math and rules with no Roblox objects in them, so they can be tested
	outside Roblox (see tests/test_logic.luau):
	odds, Equip Best, the multiplier, saved-data cleaning, formations,
	number formatting and reading the pet model lines.
]]

local PetLogic = {}

---------------------------------------------------------------------
-- Model lines (PetModels)
---------------------------------------------------------------------

local function swapSide(name: string): string
	local swapped, count = string.gsub(name, "L$", "R")
	if count == 0 then
		return name .. "R"
	end
	return swapped
end

-- Turns the text lines of a model into a list of part descriptions.
-- Parts flagged "M" get a mirrored copy for the right side.
function PetLogic.ParseModel(text: string): { any }
	local parts = {}
	for line in string.gmatch(text, "[^\n]+") do
		local t = {}
		for token in string.gmatch(line, "%S+") do
			table.insert(t, token)
		end
		if #t >= 14 then
			local part = {
				Name = t[1],
				Size = { tonumber(t[2]) or 1, tonumber(t[3]) or 1, tonumber(t[4]) or 1 },
				Pos = { tonumber(t[5]) or 0, tonumber(t[6]) or 0, tonumber(t[7]) or 0 },
				Rot = { tonumber(t[8]) or 0, tonumber(t[9]) or 0, tonumber(t[10]) or 0 },
				Color = t[11],
				Mat = t[12],
				Shape = t[13],
				Group = t[14],
				Transparency = 0,
				Mirror = false,
			}
			for i = 15, #t do
				local flag = t[i]
				if flag == "M" then
					part.Mirror = true
				elseif string.sub(flag, 1, 1) == "T" then
					part.Transparency = (tonumber(string.sub(flag, 2)) or 0) / 100
				end
			end
			table.insert(parts, part)
			if part.Mirror then
				local group = part.Group
				if string.sub(group, -1) == "L" then
					group = string.sub(group, 1, -2) .. "R"
				end
				table.insert(parts, {
					Name = swapSide(part.Name),
					Size = part.Size,
					Pos = { -part.Pos[1], part.Pos[2], part.Pos[3] },
					Rot = { part.Rot[1], -part.Rot[2], -part.Rot[3] },
					Color = part.Color,
					Mat = part.Mat,
					Shape = part.Shape,
					Group = group,
					Transparency = part.Transparency,
					Mirror = false,
				})
			end
		end
	end
	return parts
end

-- Adds the right-side pivot for every left-side group (WingL -> WingR).
function PetLogic.ExpandPivots(pivots: { [string]: { number } }): { [string]: { number } }
	local out = {}
	for name, p in pairs(pivots) do
		out[name] = p
		if string.sub(name, -1) == "L" then
			out[string.sub(name, 1, -2) .. "R"] = { -p[1], p[2], p[3] }
		end
	end
	return out
end

---------------------------------------------------------------------
-- Odds
---------------------------------------------------------------------

-- odds = { { "SnowFox", 70 }, { "IceDragon", 24 }, ... }, roll = a number from 0 up to (not including) 1
function PetLogic.PickWeighted(odds: { { any } }, roll: number): string
	local total = 0
	for _, entry in ipairs(odds) do
		total += entry[2]
	end
	local left = roll * total
	for _, entry in ipairs(odds) do
		left -= entry[2]
		if left < 0 then
			return entry[1]
		end
	end
	return odds[#odds][1]
end

function PetLogic.OddsTotal(odds: { { any } }): number
	local total = 0
	for _, entry in ipairs(odds) do
		total += entry[2]
	end
	return total
end

-- "12%", "0.5%", "0.05%"
function PetLogic.FormatPercent(value: number): string
	if value >= 10 or value == math.floor(value) then
		return string.format("%d%%", math.floor(value + 0.5))
	end
	local text = string.format("%.2f", value)
	text = string.gsub(text, "0+$", "")
	text = string.gsub(text, "%.$", "")
	return text .. "%"
end

---------------------------------------------------------------------
-- Owned pets
-- data.Pets = { { Id = "p1", Pet = "SnowFox" }, ... }, data.Equipped = { "p1", ... }
---------------------------------------------------------------------

local function idNumber(id: string): number
	return tonumber(string.match(id, "%d+") or "0") or 0
end

local function powerOf(pets, petId: string): number
	local def = pets[petId]
	return def and def.Power or 0
end

-- Strongest first; same power: oldest first (so results never jump around).
function PetLogic.SortStrongest(list: { any }, pets): { any }
	local copy = table.clone(list)
	table.sort(copy, function(a, b)
		local pa, pb = powerOf(pets, a.Pet), powerOf(pets, b.Pet)
		if pa ~= pb then
			return pa > pb
		end
		return idNumber(a.Id) < idNumber(b.Id)
	end)
	return copy
end

function PetLogic.BestIds(data, pets, maxEquipped: number): { string }
	local sorted = PetLogic.SortStrongest(data.Pets, pets)
	local out = {}
	for i = 1, math.min(maxEquipped, #sorted) do
		table.insert(out, sorted[i].Id)
	end
	return out
end

function PetLogic.EquippedSet(data): { [string]: boolean }
	local set = {}
	for _, id in ipairs(data.Equipped) do
		set[id] = true
	end
	return set
end

-- Pet types of the equipped pets, strongest first: { "Phoenix", "Phoenix", "ShadowCat" }
function PetLogic.EquippedTypes(data, pets): { string }
	local set = PetLogic.EquippedSet(data)
	local list = {}
	for _, pet in ipairs(data.Pets) do
		if set[pet.Id] then
			table.insert(list, pet)
		end
	end
	local out = {}
	for _, pet in ipairs(PetLogic.SortStrongest(list, pets)) do
		table.insert(out, pet.Pet)
	end
	return out
end

function PetLogic.Multiplier(petTypes: { string }, pets): number
	local total = 1
	for _, petId in ipairs(petTypes) do
		total += powerOf(pets, petId)
	end
	return total
end

-- counts[petId] = owned, equipped[petId] = equipped
function PetLogic.Counts(data): ({ [string]: number }, { [string]: number })
	local set = PetLogic.EquippedSet(data)
	local counts, equipped = {}, {}
	for _, pet in ipairs(data.Pets) do
		counts[pet.Pet] = (counts[pet.Pet] or 0) + 1
		if set[pet.Id] then
			equipped[pet.Pet] = (equipped[pet.Pet] or 0) + 1
		end
	end
	return counts, equipped
end

-- One pet of this type: prefer one that is (or is not) equipped.
function PetLogic.FindOfType(data, petId: string, wantEquipped: boolean?): string?
	local set = PetLogic.EquippedSet(data)
	local fallback = nil
	for i = #data.Pets, 1, -1 do
		local pet = data.Pets[i]
		if pet.Pet == petId then
			local isEquipped = set[pet.Id] == true
			if wantEquipped == nil or isEquipped == wantEquipped then
				return pet.Id
			end
			fallback = fallback or pet.Id
		end
	end
	if wantEquipped == nil then
		return fallback
	end
	return nil
end

function PetLogic.RemoveId(list: { string }, id: string): boolean
	for i, value in ipairs(list) do
		if value == id then
			table.remove(list, i)
			return true
		end
	end
	return false
end

function PetLogic.NewData(defaultFormation: string)
	return {
		Version = 1,
		Pets = {},
		Equipped = {},
		NextId = 1,
		Discovered = {},
		Formation = defaultFormation,
		Hatched = 0,
		Granted = {},
		Kept = {}, -- saved pets whose type is no longer in PetConfig (never lost)
	}
end

-- Cleans saved data: unknown pets and broken entries are dropped, nothing crashes.
function PetLogic.Sanitize(raw: any, pets, formations: { string }, defaultFormation: string)
	local data = PetLogic.NewData(defaultFormation)
	if type(raw) ~= "table" then
		return data
	end
	local seen = {}
	local highest = 0
	if type(raw.Pets) == "table" then
		for _, entry in ipairs(raw.Pets) do
			if type(entry) == "table" and type(entry.Id) == "string" and type(entry.Pet) == "string" and not seen[entry.Id] then
				seen[entry.Id] = true
				highest = math.max(highest, idNumber(entry.Id))
				if pets[entry.Pet] then
					table.insert(data.Pets, { Id = entry.Id, Pet = entry.Pet })
				else
					-- A pet type that is not in PetConfig (renamed or removed): keep it in the
					-- save so it comes back if the name is put back. It is not shown or used.
					table.insert(data.Kept, { Id = entry.Id, Pet = entry.Pet })
				end
			end
		end
	end
	if type(raw.Kept) == "table" then
		for _, entry in ipairs(raw.Kept) do
			if type(entry) == "table" and type(entry.Id) == "string" and type(entry.Pet) == "string" and not seen[entry.Id] then
				seen[entry.Id] = true
				highest = math.max(highest, idNumber(entry.Id))
				if pets[entry.Pet] then
					table.insert(data.Pets, { Id = entry.Id, Pet = entry.Pet })
				else
					table.insert(data.Kept, { Id = entry.Id, Pet = entry.Pet })
				end
			end
		end
	end
	local known = {}
	for _, pet in ipairs(data.Pets) do
		known[pet.Id] = true
	end
	if type(raw.Equipped) == "table" then
		local used = {}
		for _, id in ipairs(raw.Equipped) do
			if type(id) == "string" and known[id] and not used[id] and #data.Equipped < 12 then
				used[id] = true
				table.insert(data.Equipped, id)
			end
		end
	end
	local nextId = tonumber(raw.NextId) or 1
	data.NextId = math.max(math.floor(nextId), highest + 1)
	if type(raw.Discovered) == "table" then
		for petId, value in pairs(raw.Discovered) do
			if type(petId) == "string" and pets[petId] and value == true then
				data.Discovered[petId] = true
			end
		end
	end
	for _, pet in ipairs(data.Pets) do
		data.Discovered[pet.Pet] = true
	end
	if type(raw.Formation) == "string" and table.find(formations, raw.Formation) then
		data.Formation = raw.Formation
	end
	data.Hatched = math.max(0, math.floor(tonumber(raw.Hatched) or 0))
	if type(raw.Granted) == "table" then
		for key, value in pairs(raw.Granted) do
			if type(key) == "string" and value == true then
				data.Granted[key] = true
			end
		end
	end
	return data
end

---------------------------------------------------------------------
-- Formations
-- Offsets around the player, in the player's own space:
-- x = right, y = up, z = BEHIND the player (positive z is behind).
---------------------------------------------------------------------

function PetLogic.FormationSlots(formation: string, count: number, spacing: number, t: number): { { number } }
	local slots = {}
	if count <= 0 then
		return slots
	end
	spacing = math.max(spacing, 1)

	if formation == "Circle" then
		local radius = 3.2 + spacing * 0.9 + math.max(0, count - 4) * 0.45 * spacing
		for i = 1, count do
			local a = math.rad((i - 1) * 360 / count + t * 22)
			table.insert(slots, { math.sin(a) * radius, 0, math.cos(a) * radius })
		end
	elseif formation == "V" then
		local gap = 1.6 + spacing * 0.95
		local base = 3.0 + spacing * 0.8
		local index = 1
		if count % 2 == 1 then
			table.insert(slots, { 0, 0.4, base })
			index = 2
		end
		local k = 1
		while index <= count do
			local z = base + k * gap * 0.75
			table.insert(slots, { k * gap, 0.4 + k * 0.35, z })
			index += 1
			if index <= count then
				table.insert(slots, { -k * gap, 0.4 + k * 0.35, z })
				index += 1
			end
			k += 1
		end
	else -- "Arc": rows behind the player, 3 in the first row, then 4, 5 ...
		local placed = 0
		local row = 0
		while placed < count do
			local capacity = 3 + row
			local n = math.min(capacity, count - placed)
			local radius = 3.0 + spacing * 0.95 + row * (1.2 + spacing * 0.85)
			local spread = math.min(150, 48 * (n - 1))
			for i = 1, n do
				local angle
				if n == 1 then
					angle = if row == 0 then 32 else 0
				else
					angle = -spread / 2 + (i - 1) * spread / (n - 1)
				end
				local a = math.rad(angle)
				table.insert(slots, { math.sin(a) * radius, row * 0.6, math.cos(a) * radius })
			end
			placed += n
			row += 1
		end
	end
	return slots
end

---------------------------------------------------------------------
-- Text
---------------------------------------------------------------------

local function commas(n: number): string
	local text = tostring(math.floor(math.abs(n)))
	local out = string.reverse((string.gsub(string.reverse(text), "(%d%d%d)", "%1,")))
	if string.sub(out, 1, 1) == "," then
		out = string.sub(out, 2)
	end
	if n < 0 then
		out = "-" .. out
	end
	return out
end
PetLogic.Commas = commas

local SUFFIXES = { { 1e15, "Qa" }, { 1e12, "T" }, { 1e9, "B" }, { 1e6, "M" } }

-- 950 -> "950", 12500 -> "12,500", 2500000 -> "2.5M"
function PetLogic.FormatNumber(n: number): string
	for _, s in ipairs(SUFFIXES) do
		if math.abs(n) >= s[1] then
			local value = math.floor(n / s[1] * 10) / 10
			local text = string.format("%.1f", value)
			text = string.gsub(text, "%.0$", "")
			return text .. s[2]
		end
	end
	return commas(n)
end

-- 1 -> "x1", 26.5 -> "x26.5", 12345 -> "x12,345"
function PetLogic.FormatMultiplier(n: number): string
	if n >= 1000 then
		return "x" .. PetLogic.FormatNumber(math.floor(n))
	end
	local rounded = math.floor(n * 10 + 0.5) / 10
	local text = string.format("%.1f", rounded)
	text = string.gsub(text, "%.0$", "")
	return "x" .. text
end

-- "+0.5x", "+10x", "+2,500x"
function PetLogic.FormatPower(n: number): string
	if n == math.floor(n) then
		return "+" .. commas(n) .. "x"
	end
	return "+" .. tostring(n) .. "x"
end

-- "snow fox", "SnowFox", "snowfox" all find "SnowFox"
function PetLogic.FindPetId(input: string, pets): string?
	local function key(s: string): string
		return string.lower((string.gsub(s, "[%s_%-]", "")))
	end
	local wanted = key(input)
	for petId, def in pairs(pets) do
		if key(petId) == wanted or key(def.Name or "") == wanted then
			return petId
		end
	end
	return nil
end

-- Shortest turn from angle a to angle b (radians), smoothed by alpha.
function PetLogic.LerpAngle(a: number, b: number, alpha: number): number
	local diff = (b - a + math.pi) % (2 * math.pi) - math.pi
	return a + diff * alpha
end

return PetLogic
