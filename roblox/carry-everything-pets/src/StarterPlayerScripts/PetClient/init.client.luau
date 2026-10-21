--[[
	PetClient  (StarterPlayer > StarterPlayerScripts > PetClient, a LocalScript)

	Runs on each player's device. Its ModuleScript children do the work:
	  PetRenderer    draws and moves every player's pets
	  PetUI          the PETS button, the Pets menu and the egg panel
	  HatchCutscene  the egg opening animation
	  UIKit          shared look of the menus
]]

local PetRenderer = require(script:WaitForChild("PetRenderer"))
local PetUI = require(script:WaitForChild("PetUI"))
local HatchCutscene = require(script:WaitForChild("HatchCutscene"))

PetRenderer.Start()
PetUI.Start({ Renderer = PetRenderer, Cutscene = HatchCutscene })
