--[[
	PetConfig  (ReplicatedStorage > PetShared > PetConfig, a ModuleScript)

	Every number you may want to change is in this file:
	prices, odds, equip slots, game passes, pet power, auras and effects.
	The server and every player's device read the same file.
]]

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local PetConfig = {}

---------------------------------------------------------------------
-- 1. YOUR GAME
---------------------------------------------------------------------

-- The name of your coins value inside leaderstats (an IntValue or NumberValue).
PetConfig.CurrencyName = "Coins"
-- Also tried, in this order, when CurrencyName is not found.
PetConfig.CurrencyFallbacks = { "Coins", "Cash", "Money", "Gold" }
-- Only in Studio: if your game has no coins value yet, make leaderstats > Coins
-- with this many coins so you can test the eggs. Never happens in the live game.
PetConfig.StudioTestCoins = 1000000

---------------------------------------------------------------------
-- 2. PETS PER PLAYER
---------------------------------------------------------------------

PetConfig.MaxEquipped = 4 -- pets that follow you at the same time
PetConfig.MaxStorage = 50 -- pets you can own
PetConfig.AutoEquipNew = true -- new pets fill empty equip slots by themselves
PetConfig.StartingPets = {} -- for example { "SnowFox" } to give every new player a pet

---------------------------------------------------------------------
-- 3. GAME PASSES  (0 = turned off)
---------------------------------------------------------------------

PetConfig.GamePasses = {
	ExtraSlots = 0, -- owners get ExtraSlotsAmount more equip slots
	CrystalKing = 0, -- owners get the Crystal King (Exclusive) pet
	TripleHatch = 0, -- if 0, everyone can open 3 eggs at once
}
PetConfig.ExtraSlotsAmount = 2

---------------------------------------------------------------------
-- 4. LOOK AND MOVEMENT
---------------------------------------------------------------------

PetConfig.PetScale = 0.75 -- size of all pets (1 = model size)
PetConfig.FloatHeight = 0.6 -- how high pets float, compared to your waist
PetConfig.FollowSmoothness = 9 -- higher = pets catch up faster
PetConfig.Formations = { "Arc", "Circle", "V" }
PetConfig.DefaultFormation = "Arc"

-- Where the orange PETS button sits (move it if it covers one of your own buttons).
PetConfig.PetsButtonAnchor = Vector2.new(0, 0.5)
PetConfig.PetsButtonPosition = UDim2.new(0, 12, 0.5, -10)

---------------------------------------------------------------------
-- 5. PERFORMANCE (keeps phones smooth)
---------------------------------------------------------------------

PetConfig.Fx = {
	ParticleDistance = 85, -- particles and lightning stop further away than this (studs from the camera)
	RingDistance = 140, -- energy rings stop further away than this
	HideDistance = 260, -- whole pets hide further away than this
	MaxParticlePets = 14, -- only the nearest pets this many get particles
	OutlineBudget = 24, -- neon outlines at once (Roblox shows at most 31)
	OtherPlayersRate = 0.5, -- other players' pets use half the particles
	LowRate = 0.4, -- particle amount on the "Low" effects setting
	PhonesStartLow = true, -- phones and tablets start on "Low"
}

PetConfig.Textures = {
	Sparkle = "rbxasset://textures/particles/sparkles_main.dds",
	Fire = "rbxasset://textures/particles/fire_main.dds",
	Smoke = "rbxasset://textures/particles/smoke_main.dds",
	Spark = "rbxasset://textures/particles/fire_sparks_main.dds",
}

---------------------------------------------------------------------
-- 6. SAVING AND TESTING
---------------------------------------------------------------------

PetConfig.DataStoreName = "CarryEverything_Pets_v1"
PetConfig.AutosaveSeconds = 120
PetConfig.HatchCooldown = 0.9 -- seconds between two egg openings
PetConfig.EggRange = 14 -- how close (studs) you must stand to open an egg

-- Chat test commands: "!pet coins 100000", "!pet give Phoenix 2", "!pet reset".
-- They work for everyone in Studio, and in the live game only for these UserIds.
PetConfig.Admins = {}
PetConfig.CommandPrefix = "!pet"

-- Rarity Legendary and up: the whole server sees "X hatched a Mythic Demon Dragon!"
PetConfig.AnnounceFromOrder = 4

---------------------------------------------------------------------
-- 7. RARITIES
---------------------------------------------------------------------

PetConfig.Rarities = {
	Common = { Order = 1, Color = hex("#E6EEF7") },
	Rare = { Order = 2, Color = hex("#3DA9FF") },
	Epic = { Order = 3, Color = hex("#C36BFF") },
	Legendary = { Order = 4, Color = hex("#FFC21A") },
	Mythic = { Order = 5, Color = hex("#FF4040") },
	Celestial = { Order = 6, Color = hex("#5CF2FF") },
	Galaxy = { Order = 7, Color = hex("#FF6AD5"), Gradient = { hex("#8B7CFF"), hex("#FF6AD5") } },
	Void = { Order = 8, Color = hex("#9D5CFF"), Gradient = { hex("#6B21A8"), hex("#C77DFF") } },
	Rainbow = {
		Order = 9,
		Color = hex("#F9A8D4"),
		Gradient = { hex("#FF4D6D"), hex("#FFB020"), hex("#FFE14D"), hex("#4ADE80"), hex("#38BDF8"), hex("#A78BFA") },
	},
	Exclusive = { Order = 10, Color = hex("#9FD8FF"), Gradient = { hex("#E0F7FF"), hex("#3B82F6") }, NoDelete = true },
}

---------------------------------------------------------------------
-- 8. PETS
-- Power: added to the multiplier while the pet is equipped.
--   Multiplier = 1 + the Power of every equipped pet.
-- Scale: size of this pet compared to the others.
-- Aura:
--   Outline   neon outline color (or "Rainbow")
--   Rings     energy rings made of Beams: Radius, Width, Tilt (degrees), Y (height),
--             Colors {from, to} or "Rainbow", Spin and Precess (degrees per second)
--   Shell     glowing ForceField ball: Color, Transparency, Size (times the pet size)
--   Particles { Preset, Colors, Rate (per second), Where }
--             Presets: Sparkles, Stars, Snow, Flames, DarkFlames, Smoke, Embers,
--                      Pillar, Diamonds, Nebula, VoidPull, Breath
--             Where: "Body" (default), "Ground", or "Part:<part name>" / "Parts:<a>,<b>"
--   Lightning { Color, Bolts, Every = {min, max} seconds }
--   Orbiters  { Kind = "Star" | "Crystal" | "Diamond", Count, Radius, Y, Tilt, Speed, Color, Size }
--   Trails    { Parts = {...}, Rainbow = true }
--   HueCycle  true = shell and outline slowly cycle through all colors
---------------------------------------------------------------------

PetConfig.Pets = {
	SnowFox = {
		Name = "Snow Fox",
		Rarity = "Common",
		Power = 0.5,
		Scale = 1.0,
		Description = "A white fox with ice-blue eyes and a glowing tail tip.",
		Aura = {
			Outline = hex("#FFFFFF"),
			Rings = {
				{ Radius = 1.9, Width = 0.14, Tilt = 12, Y = 0, Colors = { hex("#FFFFFF"), hex("#BDF4FF") }, Spin = 120, Precess = 25 },
			},
			Particles = {
				{ Preset = "Sparkles", Colors = { hex("#FFFFFF"), hex("#CFF4FF") }, Rate = 6 },
				{ Preset = "Snow", Colors = { hex("#FFFFFF"), hex("#E6FBFF") }, Rate = 3 },
			},
		},
	},

	IceDragon = {
		Name = "Ice Dragon",
		Rarity = "Rare",
		Power = 1.5,
		Scale = 1.05,
		Description = "A blue dragon with ice horns, crystal spikes and see-through wings.",
		Aura = {
			Outline = hex("#3DA9FF"),
			Rings = {
				{ Radius = 2.3, Width = 0.16, Tilt = 18, Y = 0.1, Colors = { hex("#9CFFFF"), hex("#3DA9FF") }, Spin = 140, Precess = 30 },
				{ Radius = 2.7, Width = 0.12, Tilt = -32, Y = 0.1, Colors = { hex("#E6FBFF"), hex("#7FD8FF") }, Spin = -100, Precess = -20 },
			},
			Particles = {
				{ Preset = "Flames", Colors = { hex("#7FF3FF"), hex("#1E90FF") }, Rate = 9 },
				{ Preset = "Snow", Colors = { hex("#E6FBFF"), hex("#BDF4FF") }, Rate = 6 },
				{ Preset = "Breath", Colors = { hex("#CFFFFF"), hex("#7FD8FF") }, Rate = 4, Where = "Part:snout" },
			},
		},
	},

	ShadowCat = {
		Name = "Shadow Cat",
		Rarity = "Epic",
		Power = 4,
		Scale = 1.05,
		Description = "A purple cat with big glowing eyes, slit pupils and neon whiskers.",
		Aura = {
			Outline = hex("#C36BFF"),
			Rings = {
				{ Radius = 2.0, Width = 0.15, Tilt = 20, Y = 0.1, Colors = { hex("#E879F9"), hex("#7C3AED") }, Spin = 150, Precess = 35 },
				{ Radius = 2.4, Width = 0.1, Tilt = -25, Y = 0.1, Colors = { hex("#C084FC"), hex("#4C1D95") }, Spin = -120, Precess = -25 },
			},
			Shell = { Color = hex("#7C3AED"), Transparency = 0.55, Size = 1.12 },
			Particles = {
				{ Preset = "DarkFlames", Colors = { hex("#6B21A8"), hex("#12061F") }, Rate = 12 },
				{ Preset = "Smoke", Colors = { hex("#2E1065"), hex("#4C1D95") }, Rate = 3, Where = "Ground" },
				{ Preset = "Sparkles", Colors = { hex("#F0ABFC"), hex("#E879F9") }, Rate = 3, Where = "Parts:eyeL,eyeR" },
			},
		},
	},

	Phoenix = {
		Name = "Phoenix",
		Rarity = "Legendary",
		Power = 10,
		Scale = 1.1,
		Description = "A golden bird with huge fiery wings, a flame crest and long tail feathers.",
		Aura = {
			Outline = hex("#FFC21A"),
			Rings = {
				{ Radius = 2.6, Width = 0.2, Tilt = 15, Y = 0.2, Colors = { hex("#FFE066"), hex("#FF7A00") }, Spin = 160, Precess = 40 },
				{ Radius = 3.1, Width = 0.14, Tilt = -35, Y = 0.2, Colors = { hex("#FFF7CC"), hex("#FFB21A") }, Spin = -120, Precess = -25 },
				{ Radius = 3.6, Width = 0.25, Tilt = 0, Y = -1.6, Colors = { hex("#FFD000"), hex("#FF5A00") }, Spin = 60, Precess = 0 },
			},
			Shell = { Color = hex("#FFB21A"), Transparency = 0.35, Size = 1.25 },
			Particles = {
				{ Preset = "Flames", Colors = { hex("#FFD000"), hex("#FF3D00") }, Rate = 9, Where = "Parts:wing2L,wing2R" },
				{ Preset = "Flames", Colors = { hex("#FFE066"), hex("#FF5A00") }, Rate = 6, Where = "Parts:wing3L,wing3R" },
				{ Preset = "Embers", Colors = { hex("#FFE066"), hex("#FF9500") }, Rate = 8 },
				{ Preset = "Sparkles", Colors = { hex("#FFF7CC"), hex("#FFD000") }, Rate = 6 },
				{ Preset = "Pillar", Colors = { hex("#FFF7CC"), hex("#FFB21A") }, Rate = 6, Where = "Ground" },
			},
			Lightning = { Color = hex("#FFE066"), Bolts = 2, Every = { 0.6, 1.4 } },
		},
	},

	DemonDragon = {
		Name = "Demon Dragon",
		Rarity = "Mythic",
		Power = 25,
		Scale = 1.15,
		Description = "A black dragon with red neon spikes, horn tips, claws and a glowing mouth.",
		Aura = {
			Outline = hex("#FF4040"),
			Rings = {
				{ Radius = 2.8, Width = 0.2, Tilt = 20, Y = 0.2, Colors = { hex("#FF2D2D"), hex("#3B0000") }, Spin = -170, Precess = 35 },
				{ Radius = 3.3, Width = 0.14, Tilt = -30, Y = 0.2, Colors = { hex("#FF7A00"), hex("#FF0000") }, Spin = 130, Precess = -25 },
				{ Radius = 3.8, Width = 0.28, Tilt = 0, Y = -1.7, Colors = { hex("#FF1E1E"), hex("#2A0000") }, Spin = 70, Precess = 0 },
			},
			Shell = { Color = hex("#FF0000"), Transparency = 0.4, Size = 1.25 },
			Particles = {
				{ Preset = "Flames", Colors = { hex("#FF7A00"), hex("#FF0000") }, Rate = 16 },
				{ Preset = "Flames", Colors = { hex("#FF5A00"), hex("#7A0000") }, Rate = 10, Where = "Ground" },
				{ Preset = "Smoke", Colors = { hex("#1A0000"), hex("#3B0000") }, Rate = 4, Where = "Ground" },
				{ Preset = "Embers", Colors = { hex("#FF5A00"), hex("#FF2D2D") }, Rate = 8 },
			},
			Lightning = { Color = hex("#FF1E1E"), Bolts = 3, Every = { 0.3, 0.9 } },
		},
	},

	Angel = {
		Name = "Angel",
		Rarity = "Celestial",
		Power = 60,
		Scale = 1.15,
		Description = "A white angel with a golden halo, cyan eyes and glowing cyan wings.",
		Aura = {
			Outline = hex("#5CF2FF"),
			Rings = {
				{ Radius = 0.75, Width = 0.12, Tilt = 0, Y = 2.37, Colors = { hex("#FFE066"), hex("#FFF7CC") }, Spin = 90, Precess = 0 },
				{ Radius = 2.6, Width = 0.16, Tilt = 70, Y = 0.5, Colors = { hex("#5CF2FF"), hex("#FFFFFF") }, Spin = 140, Precess = 30 },
				{ Radius = 2.6, Width = 0.16, Tilt = -70, Y = 0.5, Colors = { hex("#CFFAFE"), hex("#22D3EE") }, Spin = -140, Precess = 30 },
				{ Radius = 3.5, Width = 0.22, Tilt = 0, Y = -1.5, Colors = { hex("#FFFFFF"), hex("#5CF2FF") }, Spin = 50, Precess = 0 },
			},
			Shell = { Color = hex("#5CF2FF"), Transparency = 0.45, Size = 1.25 },
			Particles = {
				{ Preset = "Stars", Colors = { hex("#FFFFFF"), hex("#5CF2FF") }, Rate = 8 },
				{ Preset = "Sparkles", Colors = { hex("#CFFAFE"), hex("#FFFFFF") }, Rate = 4, Where = "Parts:wing2L,wing2R" },
				{ Preset = "Pillar", Colors = { hex("#FFFFFF"), hex("#A5F3FC") }, Rate = 6, Where = "Ground" },
			},
			Orbiters = { Kind = "Star", Count = 5, Radius = 2.2, Y = 0.6, Tilt = 10, Speed = 50, Color = hex("#FFF7CC"), Size = 0.28 },
		},
	},

	GalaxyWolf = {
		Name = "Galaxy Wolf",
		Rarity = "Galaxy",
		Power = 150,
		Scale = 1.2,
		Description = "A cosmic wolf with a nebula stripe, star spots and glowing paws.",
		Aura = {
			Outline = hex("#FF6AD5"),
			Rings = {
				{ Radius = 2.8, Width = 0.18, Tilt = 22, Y = 0.2, Colors = { hex("#8B7CFF"), hex("#FF6AD5") }, Spin = 120, Precess = 35 },
				{ Radius = 3.2, Width = 0.12, Tilt = -40, Y = 0.2, Colors = { hex("#38BDF8"), hex("#A855F7") }, Spin = -100, Precess = -30 },
				{ Radius = 3.8, Width = 0.25, Tilt = 0, Y = -1.6, Colors = { hex("#C026D3"), hex("#3B82F6") }, Spin = 40, Precess = 0 },
			},
			Shell = { Color = hex("#8B5CF6"), Transparency = 0.4, Size = 1.3 },
			Particles = {
				{ Preset = "Nebula", Colors = { hex("#7C3AED"), hex("#EC4899") }, Rate = 3 },
				{ Preset = "Stars", Colors = { hex("#FFFFFF"), hex("#F0ABFC") }, Rate = 8 },
				{ Preset = "Sparkles", Colors = { hex("#FF6AD5"), hex("#8B7CFF") }, Rate = 5 },
			},
			Orbiters = { Kind = "Star", Count = 7, Radius = 2.6, Y = 0.4, Tilt = 25, Speed = 60, Color = hex("#FFFFFF"), Size = 0.25 },
		},
	},

	VoidBeast = {
		Name = "Void Beast",
		Rarity = "Void",
		Power = 400,
		Scale = 1.25,
		Description = "A hunched dark monster with three glowing eyes, claws and back crystals.",
		Aura = {
			Outline = hex("#9D5CFF"),
			Rings = {
				{ Radius = 2.9, Width = 0.2, Tilt = 25, Y = 0.2, Colors = { hex("#9D4EDD"), hex("#1A0B2E") }, Spin = -150, Precess = 40 },
				{ Radius = 3.4, Width = 0.16, Tilt = -20, Y = 0.2, Colors = { hex("#C77DFF"), hex("#3B0A6B") }, Spin = 110, Precess = -30 },
				{ Radius = 4.0, Width = 0.3, Tilt = 0, Y = -1.7, Colors = { hex("#6B21A8"), hex("#000000") }, Spin = -50, Precess = 0 },
			},
			Shell = { Color = hex("#3B0A6B"), Transparency = 0.25, Size = 1.3 },
			Particles = {
				{ Preset = "Flames", Colors = { hex("#C77DFF"), hex("#6B21A8") }, Rate = 14 },
				{ Preset = "VoidPull", Colors = { hex("#B57BFF"), hex("#E0B3FF") }, Rate = 10 },
				{ Preset = "Smoke", Colors = { hex("#1A0033"), hex("#3B0A6B") }, Rate = 4, Where = "Ground" },
			},
			Lightning = { Color = hex("#B57BFF"), Bolts = 2, Every = { 0.5, 1.2 } },
			Orbiters = { Kind = "Crystal", Count = 5, Radius = 2.6, Y = 0.8, Tilt = 12, Speed = 35, Color = hex("#8B3DFF"), Size = 0.5 },
		},
	},

	RainbowPegasus = {
		Name = "Rainbow Pegasus",
		Rarity = "Rainbow",
		Power = 1000,
		Scale = 1.25,
		Description = "A white winged horse with a rainbow mane and tail and glowing hooves.",
		Aura = {
			Outline = "Rainbow",
			HueCycle = true,
			Rings = {
				{ Radius = 2.8, Width = 0.2, Tilt = 18, Y = 0.3, Colors = "Rainbow", Spin = 160, Precess = 40 },
				{ Radius = 3.3, Width = 0.15, Tilt = -30, Y = 0.3, Colors = "Rainbow", Spin = -130, Precess = -30 },
				{ Radius = 4.0, Width = 0.3, Tilt = 0, Y = -1.8, Colors = "Rainbow", Spin = 60, Precess = 0 },
			},
			Shell = { Color = hex("#F9A8D4"), Transparency = 0.45, Size = 1.3 },
			Particles = {
				{ Preset = "Sparkles", Colors = "Rainbow", Rate = 12 },
				{ Preset = "Stars", Colors = { hex("#FFFFFF"), hex("#A78BFA") }, Rate = 5 },
				{ Preset = "Pillar", Colors = "Rainbow", Rate = 6, Where = "Ground" },
			},
			Trails = { Parts = { "wing3L", "wing3R", "hoofFL", "hoofFR", "hoofBL", "hoofBR" }, Rainbow = true },
		},
	},

	CrystalKing = {
		Name = "Crystal King",
		Rarity = "Exclusive",
		Power = 2500,
		Scale = 1.3,
		Description = "A crystal king with a diamond chest gem, a crystal crown and shard wings.",
		Aura = {
			Outline = hex("#9FD8FF"),
			Rings = {
				{ Radius = 2.8, Width = 0.18, Tilt = 60, Y = 0.5, Colors = { hex("#E0F7FF"), hex("#3B82F6") }, Spin = 150, Precess = 30 },
				{ Radius = 2.8, Width = 0.18, Tilt = -60, Y = 0.5, Colors = { hex("#BAE6FD"), hex("#60A5FA") }, Spin = -150, Precess = 30 },
				{ Radius = 3.4, Width = 0.14, Tilt = 0, Y = 0.5, Colors = { hex("#7DF9FF"), hex("#FFFFFF") }, Spin = 90, Precess = 0 },
				{ Radius = 4.2, Width = 0.3, Tilt = 0, Y = -1.9, Colors = { hex("#7DF9FF"), hex("#1D4ED8") }, Spin = 50, Precess = 0 },
			},
			Shell = { Color = hex("#7DD3FC"), Transparency = 0.4, Size = 1.3 },
			Particles = {
				{ Preset = "Diamonds", Colors = { hex("#E0F7FF"), hex("#7DF9FF") }, Rate = 10 },
				{ Preset = "Sparkles", Colors = { hex("#FFFFFF"), hex("#BAE6FD") }, Rate = 6 },
				{ Preset = "Pillar", Colors = { hex("#E0F7FF"), hex("#7DF9FF") }, Rate = 6, Where = "Ground" },
			},
			Orbiters = { Kind = "Diamond", Count = 6, Radius = 2.8, Y = 0.5, Tilt = 15, Speed = 45, Color = hex("#7DF9FF"), Size = 0.4 },
		},
	},
}

-- The order pets are shown in the menu (weakest first).
PetConfig.PetOrder = {
	"SnowFox",
	"IceDragon",
	"ShadowCat",
	"Phoenix",
	"DemonDragon",
	"Angel",
	"GalaxyWolf",
	"VoidBeast",
	"RainbowPegasus",
	"CrystalKing",
}

---------------------------------------------------------------------
-- 9. EGGS
-- Odds are percentages; they are shown to players before they pay.
---------------------------------------------------------------------

PetConfig.Eggs = {
	StarterEgg = {
		Name = "Starter Egg",
		Price = 250,
		Colors = { Base = hex("#E6F6FF"), Shade = hex("#BFE3F5"), Spots = { hex("#7FE7FF"), hex("#3DA9FF") } },
		Odds = {
			{ "SnowFox", 70 },
			{ "IceDragon", 24 },
			{ "ShadowCat", 5.5 },
			{ "Phoenix", 0.5 },
		},
	},
	InfernoEgg = {
		Name = "Inferno Egg",
		Price = 5000,
		Colors = { Base = hex("#FF6B1A"), Shade = hex("#D9480F"), Spots = { hex("#FFD000"), hex("#FFF3B0") } },
		Odds = {
			{ "IceDragon", 50 },
			{ "ShadowCat", 35 },
			{ "Phoenix", 12 },
			{ "DemonDragon", 2.8 },
			{ "Angel", 0.2 },
		},
	},
	CosmicEgg = {
		Name = "Cosmic Egg",
		Price = 100000,
		Colors = { Base = hex("#3A2785"), Shade = hex("#24175A"), Spots = { hex("#FF6AD5"), hex("#7DF9FF") } },
		Odds = {
			{ "Phoenix", 55 },
			{ "DemonDragon", 30 },
			{ "Angel", 12 },
			{ "GalaxyWolf", 2.5 },
			{ "VoidBeast", 0.45 },
			{ "RainbowPegasus", 0.05 },
		},
	},
}

PetConfig.EggOrder = { "StarterEgg", "InfernoEgg", "CosmicEgg" }

return PetConfig
