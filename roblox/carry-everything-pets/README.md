# Carry Everything! — Pet Aura System

10 blocky 3D pets with glowing auras for the Roblox game **Carry Everything!**
Eggs with shown odds, a Pets menu, Equip Best, Unequip All, a pet multiplier,
formations, saving, and phone-friendly menus.

Design canvas with all pets, the menus and this guide as pictures:
https://claude.ai/artifact/2oe6Q5KzeF9h1SSz5a63Cs

## The 10 pets

| Pet | Rarity | Power | Aura |
|---|---|---|---|
| Snow Fox | Common | +0.5x | white ring, sparkles, snow |
| Ice Dragon | Rare | +1.5x | 2 cyan rings, cyan flames, ice bits, frost breath |
| Shadow Cat | Epic | +4x | 2 violet rings, dark flames, shadow smoke, glowing eyes, shell |
| Phoenix | Legendary | +10x | 3 gold rings, fire on the wings, embers, gold lightning, shell |
| Demon Dragon | Mythic | +25x | 3 red rings, inferno flames, fire floor, red lightning, shell |
| Angel | Celestial | +60x | halo, crossed cyan rings, stars, 5 orbiting stars, shell |
| Galaxy Wolf | Galaxy | +150x | cosmic rings, nebula clouds, 7 orbiting stars, shell |
| Void Beast | Void | +400x | void rings, purple flames, pull-in particles, floating crystals, lightning |
| Rainbow Pegasus | Rainbow | +1,000x | rainbow rings, rainbow trails on wings and hooves, color-cycling shell |
| Crystal King | Exclusive | +2,500x | 4 ice rings, diamond particles, 6 orbiting diamonds (game pass pet) |

Multiplier = 1 + the power of every equipped pet. Example: Phoenix + Phoenix + Shadow Cat + Ice Dragon = x26.5.

Eggs (prices and odds are first guesses; change them in `PetConfig`):

| Egg | Price | Odds |
|---|---|---|
| Starter Egg | 250 | Snow Fox 70 %, Ice Dragon 24 %, Shadow Cat 5.5 %, Phoenix 0.5 % |
| Inferno Egg | 5,000 | Ice Dragon 50 %, Shadow Cat 35 %, Phoenix 12 %, Demon Dragon 2.8 %, Angel 0.2 % |
| Cosmic Egg | 100,000 | Phoenix 55 %, Demon Dragon 30 %, Angel 12 %, Galaxy Wolf 2.5 %, Void Beast 0.45 %, Rainbow Pegasus 0.05 % |

## Put it into your game (3 files)

The ready files are in `build/`:

| File | Goes into |
|---|---|
| `build/PetShared.rbxmx` | ReplicatedStorage |
| `build/PetSystem.rbxmx` | ServerScriptService |
| `build/PetClient.rbxmx` | StarterPlayer > StarterPlayerScripts |

In Roblox Studio:

1. Open your Carry Everything place. If the Explorer is hidden: **View** tab > **Explorer**.
2. Right-click **ReplicatedStorage** > **Insert from File...** > pick `PetShared.rbxmx`.
3. Right-click **ServerScriptService** > **Insert from File...** > pick `PetSystem.rbxmx`.
4. Click the little arrow next to **StarterPlayer**. Right-click **StarterPlayerScripts** > **Insert from File...** > pick `PetClient.rbxmx`.
5. **Home** > **Game Settings** > **Security** > turn on **Enable Studio Access to API Services** > **Save**.
   (Saving only works in a place that was published once: **File** > **Publish to Roblox**.)
6. Press **Play**.

Using Rojo instead? `default.project.json` maps the same three folders.

After step 4 the Explorer looks like this:

```
ReplicatedStorage
  PetShared            Folder
    PetConfig          ModuleScript   prices, odds, slots, game passes, auras  <- the file you edit
    PetModels          ModuleScript   the 10 models (one line per part)
    PetBuilder         ModuleScript   builds models, rings, particles, lightning, orbiters, trails
    PetLogic           ModuleScript   odds, Equip Best, multiplier, formations
ServerScriptService
  PetSystem            Folder
    PetServer          Script         starts everything
    PetService         ModuleScript   coins, hatching, equipping, saving, test commands
    EggStands          ModuleScript   builds the 3 egg stands
StarterPlayer
  StarterPlayerScripts
    PetClient          LocalScript
      PetRenderer      ModuleScript   pets follow, float, flap, effects get lighter far away
      PetUI            ModuleScript   PETS button, Pets menu, egg panel, messages
      HatchCutscene    ModuleScript   the egg opening
      UIKit            ModuleScript   look of the menus
```

Made by the scripts while the game runs (nothing to place by hand):
`ReplicatedStorage > PetRemotes`, `Workspace > PetEggStands` (the 3 eggs), `Workspace > LocalPets`
(each player's own copy of the pets), and `PlayerGui > PetUI`.

## Connect it to your game

**1. Your coins.** Open `PetConfig` and set `PetConfig.CurrencyName` to the name of your coins
value inside `leaderstats` (default `"Coins"`). Eggs take coins from that value.

**2. The multiplier.** Wherever your game gives strength or coins, multiply by the pet multiplier
(it is 1 without pets):

```lua
local petMult = player:GetAttribute("PetMultiplier") or 1
strength.Value += gain * petMult
```

**3. If your coins are not in leaderstats** (for example in your own data module), tell the pet
system how to read and spend them, in one of your server scripts:

```lua
local PetService = require(game.ServerScriptService.PetSystem.PetService)
PetService.SetCurrencyAdapter({
	Get = function(player) return MyData.GetCoins(player) end,
	Spend = function(player, amount) return MyData.TrySpendCoins(player, amount) end, -- true if paid
	Give = function(player, amount) MyData.AddCoins(player, amount) end, -- only for "!pet coins"
})
```

**More things your scripts can do** (server side):

```lua
PetService.GivePet(player, "Phoenix", 1)   -- rewards, codes, quests
PetService.SetBonusSlots(player, 1)        -- extra equip slots, e.g. after a rebirth
PetService.GetEquipped(player)             -- { "Phoenix", "ShadowCat", ... }
PetService.Changed.Event:Connect(function(player) ... end)
```

## Where the eggs stand

Without setup the 3 eggs stand in a row about 24 studs in front of the spawn.
To choose the spot: in **Workspace** make a **Folder** named `PetEggs`, and put 3 **Parts** in it
named `StarterEgg`, `InfernoEgg` and `CosmicEgg` where the eggs should stand. The Parts turn invisible
when the game runs.

## Test it in Studio

Type in the chat while playing in Studio:

| Command | Does |
|---|---|
| `!pet coins 100000` | gives coins |
| `!pet give Phoenix 2` | gives 2 Phoenix (any pet name works, e.g. `!pet give rainbow pegasus`) |
| `!pet reset` | removes all your pets |
| `!pet slots 2` | 2 extra equip slots |

If your game has no coins value yet, Studio makes `leaderstats > Coins` with 1,000,000 coins by itself.
In the live game these commands only work for the UserIds listed in `PetConfig.Admins`.

## Game passes (optional)

Make the pass on the Creator Hub, then put its ID into `PetConfig.GamePasses`:

- `ExtraSlots`: +2 equip slots
- `CrystalKing`: gives the Crystal King (Exclusive) pet once
- `TripleHatch`: needed for "Open 3"; leave it `0` so everyone can open 3 at once

The prices of the passes are set on the Creator Hub.
Note: the eggs cost in-game coins. If eggs are ever sold for Robux, they count as "paid random items":
the odds must stay visible (they are) and some countries do not allow them.

## Phones and speed

- Every player's device draws all pets itself, so pets move smoothly without network lag.
- Only the nearest 14 pets get particles; far pets keep only their rings; very far pets hide.
- Other players' pets use half the particles. Phones start on the "Low" effects setting.
- At most 24 neon outlines at once (Roblox can show 31).
- Players can switch **Effects: High / Low / Off** in the Pets menu.
- All numbers are in `PetConfig.Fx`.

## For developers

- Edit the files in `src/`, then run `python tools/build.py` to rebuild the `.rbxmx` files.
- Tests: `python tools/run_tests.py` (needs the `luau` command line tool; set `LUAU=` if it is not on
  the PATH; with `LUAU_LSP=` and `ROBLOX_DEFS=` it also type-checks everything against the Roblox API).
  67 tests: odds, Equip Best, multiplier, save-data cleaning, formations, config and model checks, and
  the real PetService running in a fake Roblox (hatching, coins, limits, saving, load errors, game passes,
  test commands).
- Pet models: one line per Part in `PetModels.luau` (format explained at the top of the file). The design
  canvas draws the pets from the same lines.
