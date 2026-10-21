--!nocheck
-- A tiny fake Roblox for testing PetService outside Studio.
-- tools/run_tests.py glues this file, the real module sources and test_server.luau together.

---------------------------------------------------------------------
-- Clock and task scheduler
---------------------------------------------------------------------

local now = 0
local queue = {}

local function resume(co, ...)
	local ok, err = coroutine.resume(co, ...)
	if not ok then
		error("error inside a task: " .. tostring(err) .. "\n" .. debug.traceback(co), 0)
	end
end

local task = {}
function task.spawn(fn, ...)
	local co = if type(fn) == "thread" then fn else coroutine.create(fn)
	resume(co, ...)
	return co
end
task.defer = task.spawn
function task.delay(seconds, fn, ...)
	table.insert(queue, { At = now + (seconds or 0), Co = coroutine.create(fn), Args = { ... } })
end
function task.wait(seconds)
	local co = coroutine.running()
	table.insert(queue, { At = now + (seconds or 0), Co = co, Args = {} })
	coroutine.yield()
	return seconds or 0
end

local function advance(seconds)
	local target = now + seconds
	while true do
		table.sort(queue, function(a, b)
			return a.At < b.At
		end)
		local item = queue[1]
		if not item or item.At > target then
			break
		end
		table.remove(queue, 1)
		now = math.max(now, item.At)
		resume(item.Co, table.unpack(item.Args))
	end
	now = target
end

local os = {
	clock = function()
		return now
	end,
	time = function()
		return math.floor(now)
	end,
}

local warnings = {}
local function warn(...)
	local parts = {}
	for i = 1, select("#", ...) do
		table.insert(parts, tostring(select(i, ...)))
	end
	table.insert(warnings, table.concat(parts, " "))
end
local print_real = print
local function print(...) end -- keep test output quiet

---------------------------------------------------------------------
-- Values the config needs
---------------------------------------------------------------------

local Color3 = {
	fromHex = function(hex)
		return { Hex = hex }
	end,
	fromRGB = function(r, g, b)
		return { R = r, G = g, B = b }
	end,
	new = function(r, g, b)
		return { R = r, G = g, B = b }
	end,
}
local Vector2 = { new = function(x, y)
	return { X = x, Y = y }
end }
local UDim2 = { new = function(...)
	return { ... }
end }

local Vector3Meta = {}
Vector3Meta.__index = function(v, key)
	if key == "Magnitude" then
		return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
	end
	return nil
end
Vector3Meta.__sub = function(a, b)
	return setmetatable({ X = a.X - b.X, Y = a.Y - b.Y, Z = a.Z - b.Z }, Vector3Meta)
end
Vector3Meta.__add = function(a, b)
	return setmetatable({ X = a.X + b.X, Y = a.Y + b.Y, Z = a.Z + b.Z }, Vector3Meta)
end
local Vector3 = { new = function(x, y, z)
	return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0 }, Vector3Meta)
end }

local Random = { new = function()
	return { NextNumber = function()
		return math.random()
	end }
end }

---------------------------------------------------------------------
-- Signals and instances
---------------------------------------------------------------------

local function newSignal()
	local handlers = {}
	local signal = {}
	function signal:Connect(fn)
		table.insert(handlers, fn)
		return { Disconnect = function()
			local i = table.find(handlers, fn)
			if i then
				table.remove(handlers, i)
			end
		end }
	end
	function signal:Fire(...)
		for _, fn in ipairs(table.clone(handlers)) do
			task.spawn(fn, ...)
		end
	end
	return signal
end

local InstanceMeta = {}
local Methods = {}

local function newInstance(className, name)
	local raw = { _props = { ClassName = className, Name = name or className }, _children = {}, _attrs = {} }
	return setmetatable(raw, InstanceMeta)
end

InstanceMeta.__index = function(self, key)
	if Methods[key] then
		return Methods[key]
	end
	local props = rawget(self, "_props")
	local value = props[key]
	if value ~= nil then
		return value
	end
	return nil
end
InstanceMeta.__newindex = function(self, key, value)
	local props = rawget(self, "_props")
	if key == "Parent" then
		local old = props.Parent
		if old then
			local list = rawget(old, "_children")
			local i = table.find(list, self)
			if i then
				table.remove(list, i)
			end
		end
		props.Parent = value
		if value then
			table.insert(rawget(value, "_children"), self)
		end
		return
	end
	props[key] = value
end
InstanceMeta.__tostring = function(self)
	return self.Name
end

function Methods:FindFirstChild(name)
	for _, child in ipairs(rawget(self, "_children")) do
		if child.Name == name then
			return child
		end
	end
	return nil
end
function Methods:WaitForChild(name)
	local child = self:FindFirstChild(name)
	assert(child, "WaitForChild: no " .. tostring(name) .. " in " .. tostring(self.Name))
	return child
end
function Methods:GetChildren()
	return table.clone(rawget(self, "_children"))
end
function Methods:IsA(className)
	return self.ClassName == className
end
function Methods:SetAttribute(key, value)
	rawget(self, "_attrs")[key] = value
end
function Methods:GetAttribute(key)
	return rawget(self, "_attrs")[key]
end
function Methods:Destroy()
	self.Parent = nil
end

local Instance = {}
function Instance.new(className)
	local inst = newInstance(className)
	if className == "BindableEvent" then
		inst.Event = newSignal()
		rawget(inst, "_props").Fire = nil
	elseif className == "RemoteEvent" then
		inst.Log = {}
	elseif className == "IntValue" or className == "NumberValue" then
		inst.Value = 0
	end
	return inst
end
function Methods:Fire(...)
	self.Event:Fire(...)
end
function Methods:FireClient(player, ...)
	table.insert(self.Log, { To = player, Args = { ... } })
end
function Methods:FireAllClients(...)
	table.insert(self.Log, { To = "all", Args = { ... } })
end

---------------------------------------------------------------------
-- Services
---------------------------------------------------------------------

local storeData = {}
local storeControl = { FailGet = false, FailUpdate = false, Gets = 0, Updates = 0 }
local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local out = {}
	for k, v in pairs(value) do
		out[k] = deepCopy(v)
	end
	return out
end
local fakeStore = {}
function fakeStore:GetAsync(key)
	storeControl.Gets += 1
	if storeControl.FailGet then
		error("502: mock DataStore is down")
	end
	return deepCopy(storeData[key])
end
function fakeStore:UpdateAsync(key, transform)
	storeControl.Updates += 1
	if storeControl.FailUpdate then
		error("502: mock DataStore is down")
	end
	storeData[key] = deepCopy(transform(deepCopy(storeData[key])))
end

local passOwners = {} -- [userId .. ":" .. passId] = true
local prompted = {}
local MarketplaceService = newInstance("MarketplaceService")
rawget(MarketplaceService, "_props").PromptGamePassPurchaseFinished = newSignal()
function MarketplaceService:UserOwnsGamePassAsync(userId, passId)
	return passOwners[userId .. ":" .. passId] == true
end
function MarketplaceService:PromptGamePassPurchase(player, passId)
	table.insert(prompted, { Player = player, Pass = passId })
end

local Players = newInstance("Players")
rawget(Players, "_props").PlayerAdded = newSignal()
rawget(Players, "_props").PlayerRemoving = newSignal()
local playerList = {}
function Players:GetPlayers()
	return table.clone(playerList)
end

local isStudio = true
local RunService = { IsStudio = function()
	return isStudio
end }
local DataStoreService = { GetDataStore = function()
	return fakeStore
end }

local ReplicatedStorage = newInstance("ReplicatedStorage")
local ServerScriptService = newInstance("ServerScriptService")
local closeHandlers = {}

local services = {
	Players = Players,
	DataStoreService = DataStoreService,
	MarketplaceService = MarketplaceService,
	RunService = RunService,
	ReplicatedStorage = ReplicatedStorage,
	ServerScriptService = ServerScriptService,
}
local game = {
	GetService = function(_, name)
		return assert(services[name], "mock has no service " .. name)
	end,
	BindToClose = function(_, fn)
		table.insert(closeHandlers, fn)
	end,
}

---------------------------------------------------------------------
-- Modules: the real sources are added as loaders by run_tests.py
---------------------------------------------------------------------

local loaders = {}
local loaded = {}
local function require(moduleScript)
	local name = moduleScript.Name
	if loaded[name] == nil then
		local loader = assert(loaders[name], "no module " .. name)
		loaded[name] = loader(moduleScript, require)
	end
	return loaded[name]
end

local function moduleScript(name, parent)
	local m = newInstance("ModuleScript", name)
	m.Parent = parent
	return m
end

local shared = newInstance("Folder", "PetShared")
shared.Parent = ReplicatedStorage
moduleScript("PetConfig", shared)
moduleScript("PetLogic", shared)
moduleScript("PetModels", shared)
local system = newInstance("Folder", "PetSystem")
system.Parent = ServerScriptService
moduleScript("PetService", system)
moduleScript("EggStands", system)

-- EggStands builds 3D stands; the fake just knows where they are.
local eggPositions = {}
loaders.EggStands = function()
	local EggStands = {}
	function EggStands.Build()
		eggPositions.StarterEgg = Vector3.new(0, 2, -24)
		eggPositions.InfernoEgg = Vector3.new(13, 2, -24)
		eggPositions.CosmicEgg = Vector3.new(26, 2, -24)
	end
	function EggStands.GetPosition(eggId)
		return eggPositions[eggId]
	end
	return EggStands
end

---------------------------------------------------------------------
-- Fake players
---------------------------------------------------------------------

local nextUserId = 1000
local function makePlayer(name)
	nextUserId += 1
	local player = newInstance("Player", name)
	player.UserId = nextUserId
	player.DisplayName = name
	player.Chatted = newSignal()
	local character = newInstance("Model", name)
	local root = newInstance("Part", "HumanoidRootPart")
	root.Position = Vector3.new(0, 3, -16)
	root.Parent = character
	player.Character = character
	return player
end

local function join(player)
	table.insert(playerList, player)
	player.Parent = Players
	Players.PlayerAdded:Fire(player)
end

local function leave(player)
	local i = table.find(playerList, player)
	if i then
		table.remove(playerList, i)
	end
	Players.PlayerRemoving:Fire(player)
	player.Parent = nil
end

local function moveTo(player, x, y, z)
	player.Character:FindFirstChild("HumanoidRootPart").Position = Vector3.new(x, y, z)
end

local function coins(player)
	local stats = player:FindFirstChild("leaderstats")
	local value = stats and stats:FindFirstChild("Coins")
	return value and value.Value
end
