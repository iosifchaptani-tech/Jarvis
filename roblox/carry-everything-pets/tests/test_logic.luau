--!nocheck
-- Unit tests for PetLogic (no Roblox needed). Run: python tools/run_tests.py

local PetLogic = require("../src/ReplicatedStorage/PetShared/PetLogic")

local passed, failed = 0, 0
local function test(name: string, fn: () -> ())
	local ok, err = pcall(fn)
	if ok then
		passed += 1
	else
		failed += 1
		print("FAIL " .. name .. ": " .. tostring(err))
	end
end
local function eq(a, b, msg)
	if a ~= b then
		error((msg or "") .. " expected " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end
local function near(a, b, tolerance, msg)
	if math.abs(a - b) > tolerance then
		error((msg or "") .. " expected about " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end

local PETS = {
	SnowFox = { Name = "Snow Fox", Power = 0.5 },
	IceDragon = { Name = "Ice Dragon", Power = 1.5 },
	ShadowCat = { Name = "Shadow Cat", Power = 4 },
	Phoenix = { Name = "Phoenix", Power = 10 },
	DemonDragon = { Name = "Demon Dragon", Power = 25 },
	RainbowPegasus = { Name = "Rainbow Pegasus", Power = 1000 },
}
local FORMATIONS = { "Arc", "Circle", "V" }

---------------------------------------------------------------------

test("PickWeighted picks by the edges of each chance", function()
	local odds = { { "SnowFox", 70 }, { "IceDragon", 24 }, { "ShadowCat", 5.5 }, { "Phoenix", 0.5 } }
	eq(PetLogic.PickWeighted(odds, 0), "SnowFox")
	eq(PetLogic.PickWeighted(odds, 0.6999), "SnowFox")
	eq(PetLogic.PickWeighted(odds, 0.7001), "IceDragon")
	eq(PetLogic.PickWeighted(odds, 0.9399), "IceDragon")
	eq(PetLogic.PickWeighted(odds, 0.9401), "ShadowCat")
	eq(PetLogic.PickWeighted(odds, 0.9951), "Phoenix")
	eq(PetLogic.PickWeighted(odds, 0.99999999), "Phoenix")
end)

test("PickWeighted matches the odds over many rolls", function()
	local odds = { { "A", 50 }, { "B", 35 }, { "C", 12 }, { "D", 2.8 }, { "E", 0.2 } }
	math.randomseed(42)
	local n = 200000
	local seen = {}
	for _ = 1, n do
		local pick = PetLogic.PickWeighted(odds, math.random())
		seen[pick] = (seen[pick] or 0) + 1
	end
	near(seen.A / n * 100, 50, 0.6, "A")
	near(seen.B / n * 100, 35, 0.6, "B")
	near(seen.C / n * 100, 12, 0.4, "C")
	near(seen.D / n * 100, 2.8, 0.2, "D")
	near((seen.E or 0) / n * 100, 0.2, 0.06, "E")
end)

test("FormatPercent", function()
	eq(PetLogic.FormatPercent(70), "70%")
	eq(PetLogic.FormatPercent(12), "12%")
	eq(PetLogic.FormatPercent(5.5), "5.5%")
	eq(PetLogic.FormatPercent(2.8), "2.8%")
	eq(PetLogic.FormatPercent(0.45), "0.45%")
	eq(PetLogic.FormatPercent(0.05), "0.05%")
	eq(PetLogic.FormatPercent(0.2), "0.2%")
	eq(PetLogic.FormatPercent(1), "1%")
end)

---------------------------------------------------------------------

local function sampleData()
	return {
		Pets = {
			{ Id = "p1", Pet = "SnowFox" },
			{ Id = "p2", Pet = "Phoenix" },
			{ Id = "p3", Pet = "ShadowCat" },
			{ Id = "p4", Pet = "Phoenix" },
			{ Id = "p5", Pet = "IceDragon" },
			{ Id = "p6", Pet = "SnowFox" },
		},
		Equipped = { "p1", "p5" },
	}
end

test("BestIds takes the strongest, oldest first on ties", function()
	local best = PetLogic.BestIds(sampleData(), PETS, 4)
	eq(#best, 4)
	eq(best[1], "p2")
	eq(best[2], "p4")
	eq(best[3], "p3")
	eq(best[4], "p5")
	eq(#PetLogic.BestIds(sampleData(), PETS, 10), 6)
	eq(#PetLogic.BestIds({ Pets = {}, Equipped = {} }, PETS, 4), 0)
end)

test("Multiplier is 1 + power of equipped pets (design example x26.5)", function()
	eq(PetLogic.Multiplier({}, PETS), 1)
	eq(PetLogic.Multiplier({ "Phoenix", "Phoenix", "ShadowCat", "IceDragon" }, PETS), 26.5)
	eq(PetLogic.Multiplier({ "SnowFox", "SnowFox", "SnowFox", "SnowFox" }, PETS), 3)
	eq(PetLogic.Multiplier({ "NotAPet" }, PETS), 1)
end)

test("EquippedTypes lists equipped pets strongest first", function()
	local data = sampleData()
	data.Equipped = { "p1", "p2", "p5" }
	local types = PetLogic.EquippedTypes(data, PETS)
	eq(table.concat(types, ","), "Phoenix,IceDragon,SnowFox")
end)

test("Counts", function()
	local counts, equipped = PetLogic.Counts(sampleData())
	eq(counts.SnowFox, 2)
	eq(counts.Phoenix, 2)
	eq(equipped.SnowFox, 1)
	eq(equipped.IceDragon, 1)
	eq(equipped.Phoenix, nil)
end)

test("FindOfType prefers the asked equipped state", function()
	local data = sampleData()
	eq(PetLogic.FindOfType(data, "SnowFox", false), "p6")
	eq(PetLogic.FindOfType(data, "SnowFox", true), "p1")
	eq(PetLogic.FindOfType(data, "IceDragon", false), nil)
	eq(PetLogic.FindOfType(data, "IceDragon", true), "p5")
	eq(PetLogic.FindOfType(data, "Angel", nil), nil)
end)

test("RemoveId", function()
	local list = { "a", "b", "c" }
	eq(PetLogic.RemoveId(list, "b"), true)
	eq(table.concat(list, ","), "a,c")
	eq(PetLogic.RemoveId(list, "zz"), false)
end)

---------------------------------------------------------------------

test("Sanitize: nothing or garbage gives empty data", function()
	for _, raw in ipairs({ nil, 5, "hello", {} :: any, { Pets = "x", Equipped = 3 } }) do
		local data = PetLogic.Sanitize(raw, PETS, FORMATIONS, "Arc")
		eq(#data.Pets, 0)
		eq(#data.Equipped, 0)
		eq(data.NextId, 1)
		eq(data.Formation, "Arc")
	end
end)

test("Sanitize drops unknown pets, duplicates and broken equips", function()
	local raw = {
		Pets = {
			{ Id = "p1", Pet = "SnowFox" },
			{ Id = "p2", Pet = "OldRemovedPet" },
			{ Id = "p1", Pet = "Phoenix" }, -- duplicate id
			{ Id = "p9", Pet = "Phoenix" },
			{ Pet = "Phoenix" }, -- no id
			"junk",
		},
		Equipped = { "p1", "p2", "p9", "p9", "nope", 7 },
		NextId = 3,
		Discovered = { SnowFox = true, Ghost = true, Phoenix = "yes" },
		Formation = "Spiral",
		Hatched = -4,
		Granted = { CrystalKing = true, [5] = true },
	}
	local data = PetLogic.Sanitize(raw, PETS, FORMATIONS, "Arc")
	eq(#data.Pets, 2)
	eq(data.Pets[1].Id, "p1")
	eq(data.Pets[2].Id, "p9")
	eq(table.concat(data.Equipped, ","), "p1,p9")
	eq(data.NextId, 10, "NextId must be above the highest id")
	eq(data.Discovered.SnowFox, true)
	eq(data.Discovered.Phoenix, true, "owned pets count as found")
	eq(data.Discovered.Ghost, nil)
	eq(data.Formation, "Arc")
	eq(data.Hatched, 0)
	eq(data.Granted.CrystalKing, true)
end)

test("Sanitize keeps good data as it is", function()
	local raw = {
		Pets = { { Id = "p1", Pet = "SnowFox" }, { Id = "p2", Pet = "Phoenix" } },
		Equipped = { "p2" },
		NextId = 3,
		Discovered = { SnowFox = true, Phoenix = true, IceDragon = true },
		Formation = "V",
		Hatched = 12,
		Granted = {},
	}
	local data = PetLogic.Sanitize(raw, PETS, FORMATIONS, "Arc")
	eq(#data.Pets, 2)
	eq(data.Equipped[1], "p2")
	eq(data.NextId, 3)
	eq(data.Discovered.IceDragon, true)
	eq(data.Formation, "V")
	eq(data.Hatched, 12)
end)

---------------------------------------------------------------------

test("FormationSlots: right count, spread out, behind the player", function()
	for _, formation in ipairs(FORMATIONS) do
		for count = 1, 8 do
			for _, spacing in ipairs({ 1.5, 3, 5 }) do
				local slots = PetLogic.FormationSlots(formation, count, spacing, 1.3)
				eq(#slots, count, formation .. " count")
				for i = 1, count do
					local a = slots[i]
					local fromPlayer = math.sqrt(a[1] ^ 2 + a[3] ^ 2)
					assert(fromPlayer >= 3, formation .. " slot too close to the player: " .. fromPlayer)
					if formation ~= "Circle" then
						assert(a[3] > 0, formation .. " slot must be behind the player")
					end
					for j = i + 1, count do
						local b = slots[j]
						local d = math.sqrt((a[1] - b[1]) ^ 2 + (a[2] - b[2]) ^ 2 + (a[3] - b[3]) ^ 2)
						assert(d >= spacing * 0.9, ("%s %d pets: slots %d and %d only %.2f apart"):format(formation, count, i, j, d))
					end
				end
			end
		end
	end
	eq(#PetLogic.FormationSlots("Arc", 0, 2, 0), 0)
end)

test("FormationSlots: V is mirrored left and right", function()
	local slots = PetLogic.FormationSlots("V", 4, 2, 0)
	near(slots[1][1], -slots[2][1], 1e-9)
	near(slots[1][3], slots[2][3], 1e-9)
end)

---------------------------------------------------------------------

test("Number text", function()
	eq(PetLogic.Commas(0), "0")
	eq(PetLogic.Commas(250), "250")
	eq(PetLogic.Commas(5000), "5,000")
	eq(PetLogic.Commas(100000), "100,000")
	eq(PetLogic.Commas(1234567), "1,234,567")
	eq(PetLogic.FormatNumber(950), "950")
	eq(PetLogic.FormatNumber(12500), "12,500")
	eq(PetLogic.FormatNumber(2500000), "2.5M")
	eq(PetLogic.FormatNumber(3000000), "3M")
	eq(PetLogic.FormatNumber(7.25e9), "7.2B")
	eq(PetLogic.FormatMultiplier(1), "x1")
	eq(PetLogic.FormatMultiplier(26.5), "x26.5")
	eq(PetLogic.FormatMultiplier(3.04), "x3")
	eq(PetLogic.FormatMultiplier(12345), "x12,345")
	eq(PetLogic.FormatPower(0.5), "+0.5x")
	eq(PetLogic.FormatPower(2500), "+2,500x")
end)

test("FindPetId understands names and ids", function()
	eq(PetLogic.FindPetId("snow fox", PETS), "SnowFox")
	eq(PetLogic.FindPetId("SnowFox", PETS), "SnowFox")
	eq(PetLogic.FindPetId("RAINBOW_PEGASUS", PETS), "RainbowPegasus")
	eq(PetLogic.FindPetId("dragon", PETS), nil)
end)

test("LerpAngle takes the short way round", function()
	local a = PetLogic.LerpAngle(math.rad(170), math.rad(-170), 1)
	near(math.cos(a), math.cos(math.rad(-170)), 1e-9)
	local half = PetLogic.LerpAngle(math.rad(170), math.rad(-170), 0.5)
	near(math.abs(half), math.pi, 1e-9)
end)

---------------------------------------------------------------------

test("ParseModel reads lines and mirrors parts", function()
	local parts = PetLogic.ParseModel([[
body 1 2 3 0 0 0.5 0 0 0 FFFFFF P B -
earL 0.25 0.75 0.5 -0.5 1.85 -1.15 10 90 -5 F4F8FF N W WingL M T25
too short line
]])
	eq(#parts, 3)
	eq(parts[1].Name, "body")
	eq(parts[1].Size[3], 3)
	eq(parts[2].Name, "earL")
	eq(parts[2].Transparency, 0.25)
	eq(parts[3].Name, "earR")
	eq(parts[3].Pos[1], 0.5)
	eq(parts[3].Rot[1], 10)
	eq(parts[3].Rot[2], -90)
	eq(parts[3].Rot[3], 5)
	eq(parts[3].Group, "WingR")
	eq(parts[3].Mat, "N")
	local pivots = PetLogic.ExpandPivots({ Head = { 0, 1, 0 }, WingL = { -1, 2, 3 } })
	eq(pivots.WingR[1], 1)
	eq(pivots.WingR[3], 3)
	eq(pivots.HeadR, nil)
end)

print(("%d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("tests failed")
end
