--[[
	PetModels  (ReplicatedStorage > PetShared > PetModels, a ModuleScript)

	The 10 blocky pet models. Each line is one Part:
	  name  sizeX sizeY sizeZ  posX posY posZ  rotX rotY rotZ  color  material  shape  group  [flags]

	  material  P = SmoothPlastic, N = Neon, G = Glass, I = Ice
	  shape     B = Block, W = Wedge (flat bottom, upright back, slope to the front)
	  group     "-" = body; Head nods, Tail wags, WingL/WingR flap
	  flags     M = also make the mirrored right-side part (name ...L becomes ...R)
	            T25 = 25 % see-through

	Sizes are in studs at scale 1. The front of every pet is -Z (where it looks).
	The same lines draw the pets on the design canvas, so both always match.

	Pivots: the hinge point of each moving group. WingR is mirrored from WingL.
	WingAxis: "Z" = wings at the sides flap up and down, "Y" = back wings sweep.
]]

local PetModels = {}

PetModels.SnowFox = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.55, -0.85 }, Tail = { 0, 0.25, 1.15 } },
	Parts = [[
body 1.6 1.3 2.2 0 0 0.1 0 0 0 F4F8FF P B -
chest 1.2 0.9 0.4 0 -0.05 -1.05 0 0 0 FFFFFF P B -
collar 1.7 0.22 0.5 0 0.38 -0.92 0 0 0 BDF4FF N B -
legFL 0.42 0.5 0.42 -0.5 -0.8 -0.65 0 0 0 E9F1FA P B - M
legBL 0.42 0.5 0.42 -0.5 -0.8 0.75 0 0 0 E9F1FA P B - M
head 1.6 1.4 1.4 0 0.85 -1.15 0 0 0 F8FBFF P B Head
snout 0.8 0.55 0.6 0 0.55 -2.0 0 0 0 FFFFFF P B Head
nose 0.3 0.22 0.12 0 0.78 -2.32 0 0 0 2B2F3A P B Head
eyeL 0.32 0.36 0.08 -0.4 1.05 -1.88 0 0 0 7FE7FF N B Head M
cheekL 0.3 0.5 0.6 -0.9 0.55 -1.2 0 0 0 FFFFFF P B Head M
earL 0.25 0.75 0.5 -0.5 1.85 -1.15 0 90 0 F4F8FF P W Head M
innerEarL 0.1 0.5 0.3 -0.45 1.78 -1.31 0 90 0 FFB8D9 P W Head M
tail1 0.7 0.7 1.0 0 0.35 1.6 -20 0 0 F4F8FF P B Tail
tail2 0.85 0.85 0.9 0 0.75 2.3 -35 0 0 FFFFFF P B Tail
tailTip 0.6 0.6 0.5 0 1.1 2.8 -45 0 0 E6FBFF N B Tail
]],
}

PetModels.IceDragon = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.6, -1.0 }, Tail = { 0, 0.0, 1.3 }, WingL = { -0.85, 0.65, 0.0 } },
	Parts = [[
body 1.8 1.5 2.4 0 0 0.1 0 0 0 3A8DFF P B -
belly 1.3 1.1 0.2 0 -0.1 -1.12 0 0 0 BFE9FF P B -
spike1 0.2 0.55 0.55 0 1.0 -0.45 0 0 0 9CFFFF N W -
spike2 0.2 0.6 0.6 0 1.02 0.35 0 0 0 9CFFFF N W -
spike3 0.2 0.5 0.5 0 0.97 1.05 0 0 0 9CFFFF N W -
legFL 0.5 0.6 0.5 -0.6 -0.95 -0.7 0 0 0 2F7AE6 P B - M
legBL 0.5 0.6 0.5 -0.6 -0.95 0.8 0 0 0 2F7AE6 P B - M
head 1.5 1.3 1.5 0 0.95 -1.35 0 0 0 4A9BFF P B Head
snout 1.1 0.6 0.8 0 0.6 -2.4 0 0 0 5AA8FF P B Head
eyeL 0.3 0.3 0.08 -0.45 1.15 -2.12 0 0 0 9CFFFF N B Head M
browL 0.5 0.14 0.2 -0.45 1.4 -2.05 0 0 -15 1F5FCC P B Head M
hornL 0.2 0.8 0.45 -0.45 1.85 -1.0 25 0 0 E6FBFF I W Head M
wingBoneL 1.6 0.18 0.25 -1.65 0.95 -0.1 0 0 -20 2F6FDB P B WingL M
wingMemL 1.5 0.08 1.1 -1.6 0.85 0.45 0 0 -20 7FD8FF N B WingL M T25
wingMem2L 1.0 0.08 0.8 -2.45 1.2 0.5 0 0 -25 BDF4FF N B WingL M T25
wingTipL 0.6 0.15 0.15 -2.6 1.35 -0.1 0 0 -30 E6FBFF N B WingL M
tail1 0.8 0.7 1.0 0 0.0 1.75 0 0 0 3A8DFF P B Tail
tail2 0.6 0.5 0.9 0 0.15 2.6 -8 0 0 3A8DFF P B Tail
tail3 0.4 0.35 0.7 0 0.3 3.3 -12 0 0 4A9BFF P B Tail
tailFin 0.15 0.6 0.6 0 0.65 3.4 0 0 0 9CFFFF N W Tail
]],
}

PetModels.ShadowCat = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.45, -0.75 }, Tail = { 0, 0.3, 1.1 } },
	Parts = [[
body 1.5 1.2 2.0 0 0 0.1 0 0 0 5B2A86 P B -
collar 1.6 0.2 0.45 0 0.25 -0.82 0 0 0 1A0B2E P B -
gem 0.26 0.26 0.12 0 0.08 -1.08 0 0 45 F0ABFC N B -
legFL 0.4 0.45 0.4 -0.45 -0.8 -0.55 0 0 0 3B1A5C P B - M
legBL 0.4 0.45 0.4 -0.45 -0.8 0.65 0 0 0 3B1A5C P B - M
head 1.5 1.3 1.3 0 0.8 -1.0 0 0 0 6A2FA0 P B Head
muzzle 0.7 0.4 0.25 0 0.45 -1.72 0 0 0 8B4FC4 P B Head
nose 0.22 0.16 0.08 0 0.62 -1.87 0 0 0 FF6AD5 P B Head
eyeL 0.4 0.42 0.08 -0.38 0.95 -1.68 0 0 0 F0ABFC N B Head M
pupilL 0.08 0.32 0.04 -0.38 0.95 -1.73 0 0 0 1A0B2E P B Head M
whiskerL 0.55 0.05 0.05 -0.65 0.5 -1.74 0 0 -10 E9D5FF N B Head M
earL 0.25 0.7 0.55 -0.5 1.75 -0.95 0 90 0 4A1F70 P W Head M
innerEarL 0.1 0.45 0.3 -0.45 1.68 -1.12 0 90 0 E879F9 N W Head M
tail1 0.35 0.35 0.8 0 0.4 1.45 0 0 0 5B2A86 P B Tail
tail2 0.35 0.9 0.35 0 0.95 1.7 0 0 0 5B2A86 P B Tail
tailTip 0.4 0.45 0.4 0 1.55 1.7 0 0 0 C026D3 N B Tail
]],
}

PetModels.Phoenix = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.75, -0.4 }, Tail = { 0, -0.1, 0.95 }, WingL = { -0.7, 0.4, 0.0 } },
	Parts = [[
body 1.5 1.6 1.8 0 0 0.1 0 0 0 FFB21A P B -
chest 1.1 1.1 0.2 0 -0.1 -0.85 0 0 0 FFE08A P B -
legL 0.2 0.45 0.2 -0.35 -0.95 0 0 0 0 FF7A00 P B - M
head 1.2 1.1 1.1 0 1.15 -0.65 0 0 0 FFC233 P B Head
beak 0.45 0.35 0.55 0 1.0 -1.45 0 0 0 FF7A00 P W Head
eyeL 0.22 0.26 0.08 -0.33 1.25 -1.22 0 0 0 FFF7CC N B Head M
crest1 0.15 0.7 0.6 0 1.95 -0.5 0 0 0 FF5A00 N W Head
crest2 0.15 0.5 0.45 0 1.85 -0.05 0 0 0 FFD000 N W Head
wing1L 1.3 0.18 1.1 -1.3 0.55 0.1 0 0 -15 FF9500 P B WingL M
wing2L 1.2 0.14 0.9 -2.4 0.85 0.15 0 0 -22 FF5A00 N B WingL M
wing3L 0.9 0.12 0.6 -3.25 1.2 0.2 0 0 -30 FFD000 N B WingL M
tail1 0.35 0.1 1.6 0 -0.25 1.7 15 0 0 FF7A00 N B Tail
tail2L 0.3 0.1 1.4 -0.4 -0.2 1.6 15 -20 0 FF5A00 N B Tail M
tail3 0.25 0.1 0.6 0 -0.6 2.55 25 0 0 FFD000 N B Tail
]],
}

PetModels.DemonDragon = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.65, -1.05 }, Tail = { 0, 0, 1.35 }, WingL = { -0.9, 0.7, 0.0 } },
	Parts = [[
body 1.9 1.6 2.5 0 0 0.1 0 0 0 1A1A1F P B -
belly 1.3 1.1 0.2 0 -0.1 -1.17 0 0 0 8B0F14 P B -
spike1 0.2 0.6 0.55 0 1.05 -0.6 0 0 0 FF2D2D N W -
spike2 0.2 0.7 0.65 0 1.1 0.2 0 0 0 FF2D2D N W -
spike3 0.2 0.55 0.5 0 1.02 1.0 0 0 0 FF2D2D N W -
legFL 0.55 0.65 0.55 -0.65 -1.0 -0.75 0 0 0 141418 P B - M
legBL 0.55 0.65 0.55 -0.65 -1.0 0.85 0 0 0 141418 P B - M
clawFL 0.6 0.15 0.25 -0.65 -1.3 -1.05 0 0 0 FF2D2D N B - M
head 1.6 1.35 1.6 0 1.0 -1.4 0 0 0 222228 P B Head
snout 1.2 0.65 0.9 0 0.62 -2.45 0 0 0 2A2A30 P B Head
mouth 1.0 0.1 0.12 0 0.4 -2.9 0 0 0 FF3B1F N B Head
eyeL 0.38 0.2 0.08 -0.45 1.15 -2.22 0 0 -12 FF1E1E N B Head M
hornL 0.3 0.75 0.3 -0.55 1.95 -1.1 20 0 15 0D0D10 P B Head M
hornTipL 0.22 0.6 0.22 -0.72 2.5 -0.85 45 0 25 FF2D2D N B Head M
wingBoneL 1.8 0.2 0.25 -1.8 1.0 -0.1 0 0 -22 111114 P B WingL M
wingMemL 1.7 0.08 1.3 -1.75 0.9 0.55 0 0 -22 8B0000 P B WingL M
wingMem2L 1.2 0.08 0.9 -2.75 1.3 0.55 0 0 -28 B3121B P B WingL M
wingClawL 0.5 0.18 0.18 -2.85 1.55 -0.1 0 0 -35 FF2D2D N B WingL M
tail1 0.85 0.75 1.1 0 0 1.85 0 0 0 1A1A1F P B Tail
tail2 0.65 0.55 1.0 0 0.15 2.85 -8 0 0 1A1A1F P B Tail
tail3 0.45 0.4 0.8 0 0.3 3.7 -12 0 0 222228 P B Tail
tailBlade 0.15 0.75 0.7 0 0.6 3.95 0 0 0 FF2D2D N W Tail
]],
}

PetModels.Angel = {
	WingAxis = "Y",
	Pivots = { Head = { 0, 0.75, 0 }, WingL = { -0.45, 0.45, 0.45 } },
	Parts = [[
robe 1.3 1.1 1.0 0 -0.55 0 0 0 0 FFFFFF P B -
robeTop 1.1 0.65 0.85 0 0.25 0 0 0 0 F8FCFF P B -
sash 1.14 0.16 0.89 0 -0.02 0 0 0 0 5CF2FF N B -
hem 1.34 0.12 1.04 0 -1.06 0 0 0 0 FFE066 N B -
armL 0.3 0.75 0.3 -0.72 0.05 -0.05 0 0 -15 FFFFFF P B - M
handL 0.3 0.25 0.3 -0.84 -0.4 -0.05 0 0 -15 FDE7D6 P B - M
head 1.3 1.2 1.2 0 1.17 0 0 0 0 FDE7D6 P B Head
hair 1.42 0.45 1.32 0 1.72 0.05 0 0 0 FFF3C4 P B Head
hairBack 1.42 0.9 0.3 0 1.32 0.6 0 0 0 FFF3C4 P B Head
bangL 0.35 0.25 0.2 -0.45 1.52 -0.6 0 0 0 FFF3C4 P B Head M
eyeL 0.2 0.28 0.06 -0.3 1.15 -0.62 0 0 0 5CF2FF N B Head M
blushL 0.22 0.08 0.04 -0.45 0.97 -0.61 0 0 0 FFB3C7 P B Head M
smile 0.24 0.06 0.04 0 0.89 -0.61 0 0 0 C2410C P B Head
haloF 1.0 0.12 0.12 0 2.37 -0.44 0 0 0 FFE066 N B Head
haloB 1.0 0.12 0.12 0 2.37 0.44 0 0 0 FFE066 N B Head
haloSideL 0.12 0.12 0.76 -0.44 2.37 0 0 0 0 FFE066 N B Head M
wing1L 1.3 0.9 0.15 -1.0 0.75 0.6 0 20 -15 A5F3FC N B WingL M T10
wing2L 1.0 0.65 0.12 -1.75 1.15 0.75 0 25 -25 22D3EE N B WingL M T10
wing3L 0.6 0.4 0.1 -2.3 1.5 0.85 0 25 -35 CFFAFE N B WingL M
]],
}

PetModels.GalaxyWolf = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.6, -1.1 }, Tail = { 0, 0.3, 1.3 } },
	Parts = [[
body 1.7 1.35 2.5 0 0 0.1 0 0 0 2A1B5E P B -
mane 1.85 1.0 0.6 0 0.4 -0.95 0 0 0 4C2FA8 P B -
chest 1.3 0.9 0.3 0 -0.15 -1.3 0 0 0 6D3BD8 P B -
stripe 0.7 0.1 2.2 0 0.71 0.25 0 0 0 C026D3 N B - T15
starA 0.16 0.16 0.16 -0.86 0.25 -0.2 0 0 45 FFFFFF N B - M
starB 0.14 0.14 0.14 -0.86 -0.2 0.7 0 0 45 F0ABFC N B - M
legFL 0.45 0.6 0.45 -0.55 -0.95 -0.8 0 0 0 22164F P B - M
legBL 0.45 0.6 0.45 -0.55 -0.95 0.9 0 0 0 22164F P B - M
pawFL 0.5 0.15 0.5 -0.55 -1.25 -0.8 0 0 0 7DF9FF N B - M
pawBL 0.5 0.15 0.5 -0.55 -1.25 0.9 0 0 0 7DF9FF N B - M
head 1.5 1.3 1.4 0 0.95 -1.5 0 0 0 33227A P B Head
snout 0.85 0.6 0.85 0 0.65 -2.6 0 0 0 3B2A8A P B Head
nose 0.3 0.2 0.12 0 0.88 -3.06 0 0 0 0B0620 P B Head
eyeL 0.34 0.24 0.08 -0.4 1.15 -2.22 0 0 -8 7DF9FF N B Head M
earL 0.25 0.85 0.5 -0.5 1.95 -1.35 0 90 0 2A1B5E P W Head M
innerEarL 0.1 0.55 0.3 -0.45 1.88 -1.51 0 90 0 EC4899 N W Head M
tail1 0.6 0.6 1.0 0 0.45 1.75 -20 0 0 3B2A8A P B Tail
tail2 0.7 0.7 0.9 0 0.85 2.45 -30 0 0 6D3BD8 P B Tail
tail3 0.5 0.5 0.5 0 1.2 3.0 -40 0 0 EC4899 N B Tail
]],
}

PetModels.VoidBeast = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 0.5, -0.9 }, Tail = { 0, -0.2, 1.0 } },
	Parts = [[
body 2.0 1.7 2.0 0 0 0.1 0 0 0 0E0A1A P B -
hump 1.6 0.8 1.2 0 0.95 -0.1 0 0 0 150F26 P B -
crystal1 0.3 0.9 0.7 0 1.7 -0.2 0 0 0 8B3DFF N W -
crystal2L 0.25 0.7 0.55 -0.5 1.55 0.25 0 0 20 B57BFF N W - M
armL 0.6 1.2 0.6 -1.15 -0.3 -0.6 15 0 -10 150F26 P B - M
clawL 0.7 0.25 0.35 -1.25 -0.95 -0.95 0 0 0 9D4EDD N B - M
legBL 0.5 0.6 0.6 -0.7 -1.05 0.6 0 0 0 0E0A1A P B - M
head 1.4 1.1 1.2 0 0.6 -1.45 0 0 0 120C22 P B Head
jaw 1.2 0.35 0.9 0 -0.02 -1.55 0 0 0 0A0712 P B Head
mouth 1.0 0.1 0.1 0 0.19 -2.02 0 0 0 C77DFF N B Head
eyeL 0.25 0.25 0.08 -0.38 0.72 -2.07 0 0 0 C77DFF N B Head M
eye3 0.25 0.25 0.08 0 0.98 -2.07 0 0 45 E0B3FF N B Head
hornL 0.25 0.8 0.25 -0.55 1.25 -1.3 -20 0 25 2A1D45 P B Head M
hornTipL 0.18 0.45 0.18 -0.82 1.68 -1.48 -40 0 35 8B3DFF N B Head M
tail1 0.6 0.5 0.9 0 -0.3 1.45 0 0 0 0E0A1A P B Tail
tail2 0.4 0.35 0.8 0 -0.4 2.2 0 0 0 150F26 P B Tail
tailGem 0.35 0.35 0.35 0 -0.4 2.75 45 45 0 B57BFF N B Tail
]],
}

PetModels.RainbowPegasus = {
	WingAxis = "Z",
	Pivots = { Head = { 0, 1.3, -1.25 }, Tail = { 0, 0.3, 1.2 }, WingL = { -0.8, 0.5, -0.2 } },
	Parts = [[
body 1.6 1.4 2.4 0 0 0.1 0 0 0 FFFFFF P B -
neck 0.8 1.2 0.8 0 0.9 -1.05 -25 0 0 FFFFFF P B -
mane1 0.3 0.5 0.5 0 2.05 -1.05 -25 0 0 FF4D6D N B -
mane2 0.3 0.5 0.5 0 1.68 -0.82 -25 0 0 FFB020 N B -
mane3 0.3 0.45 0.45 0 1.32 -0.64 -25 0 0 FFE14D N B -
mane4 0.3 0.4 0.45 0 0.98 -0.47 -25 0 0 4ADE80 N B -
legFL 0.4 0.9 0.4 -0.5 -1.1 -0.85 0 0 0 FFFFFF P B - M
legBL 0.4 0.9 0.4 -0.5 -1.1 0.85 0 0 0 FFFFFF P B - M
hoofFL 0.46 0.2 0.46 -0.5 -1.6 -0.85 0 0 0 A78BFA N B - M
hoofBL 0.46 0.2 0.46 -0.5 -1.6 0.85 0 0 0 38BDF8 N B - M
head 0.95 0.95 1.5 0 1.75 -1.75 0 0 0 FFFFFF P B Head
muzzle 0.85 0.6 0.55 0 1.52 -2.6 0 0 0 FFE4F1 P B Head
eyeL 0.06 0.28 0.28 -0.48 1.9 -1.95 0 0 0 38BDF8 N B Head M
earL 0.12 0.35 0.25 -0.3 2.35 -1.3 0 90 0 FFFFFF P W Head M
forelock 0.3 0.35 0.35 0 2.25 -1.9 0 0 0 F472B6 N B Head
wing1L 1.4 0.15 1.0 -1.45 0.75 -0.1 0 0 -18 FFFFFF P B WingL M
wing2L 1.2 0.12 0.8 -2.55 1.1 0.0 0 0 -25 F9A8D4 N B WingL M
wing3L 0.8 0.1 0.55 -3.3 1.45 0.05 0 0 -32 C4B5FD N B WingL M
tail1L 0.3 0.3 1.0 -0.15 0.1 1.65 30 0 0 F472B6 N B Tail M
tail2 0.3 0.3 1.1 0 0.05 1.75 38 0 0 FACC15 N B Tail
tail3 0.3 0.3 0.9 0 -0.25 1.6 48 0 0 38BDF8 N B Tail
]],
}

PetModels.CrystalKing = {
	WingAxis = "Y",
	Pivots = { Head = { 0, 0.7, 0 }, WingL = { -0.55, 0.6, 0.5 } },
	Parts = [[
torso 1.5 1.5 1.2 0 0 0 0 0 0 1D4ED8 G B -
chestGem 0.7 0.7 0.2 0 0.1 -0.62 0 0 45 7DF9FF N B -
belt 1.56 0.18 1.26 0 -0.55 0 0 0 0 BFE6FF N B -
shoulderL 0.65 0.65 0.65 -0.95 0.55 0 0 45 0 60A5FA G B - M
armL 0.4 0.9 0.4 -0.95 -0.15 0 0 0 0 1E3A8A P B - M
fistL 0.45 0.45 0.45 -0.95 -0.75 -0.05 45 45 0 7DD3FC N B - M
base 0.9 0.9 0.9 0 -1.05 0 45 0 45 3B82F6 G B -
head 1.3 1.2 1.2 0 1.35 0 0 0 0 2563EB G B Head
visor 1.1 0.3 0.06 0 1.35 -0.62 0 0 0 0B1640 P B Head
eyeL 0.3 0.16 0.07 -0.3 1.35 -0.66 0 0 0 E0F7FF N B Head M
crownBase 1.4 0.25 1.3 0 2.05 0 0 0 0 93C5FD G B Head
crownF 0.28 0.55 0.28 0 2.42 -0.5 0 45 0 7DF9FF N B Head
crownFL 0.22 0.42 0.22 -0.52 2.36 -0.45 0 45 0 BAE6FF N B Head M
crownBL 0.22 0.42 0.22 -0.52 2.36 0.45 0 45 0 BAE6FF N B Head M
crownB 0.25 0.48 0.25 0 2.4 0.5 0 45 0 7DF9FF N B Head
wingShard1L 0.25 1.8 0.25 -1.19 1.37 0.7 0 0 40 7DF9FF N B WingL M T10
wingShard2L 0.2 1.4 0.2 -1.3 0.87 0.75 0 0 70 38BDF8 N B WingL M T10
wingShard3L 0.2 1.1 0.2 -1.18 0.43 0.75 0 0 105 BAE6FF N B WingL M T10
wingSheetL 1.1 1.0 0.05 -1.1 0.95 0.8 0 0 20 BAE6FF N B WingL M T55
]],
}

return PetModels
