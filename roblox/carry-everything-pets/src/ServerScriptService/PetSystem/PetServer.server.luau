--[[
	PetServer  (ServerScriptService > PetSystem > PetServer, a Script)

	Starts the pet system: makes the remotes, builds the egg stands,
	loads and saves every player's pets.
	All the work is in the PetService ModuleScript next to this Script.
]]

local PetService = require(script.Parent:WaitForChild("PetService"))

PetService.Start()
