# Rumble Nation Simulator

Win the game by strategically deploying your forces and planning your strategy to achieve a higher total score than all other players when the game ends.

## Core Gameplay

### 0. Game Setup

Before the game begins, number tokens representing 2 through 12 are randomly assigned to 11 regions on the map. This determines the base point value of each region, the dice combination required to select it during the deployment phase, and the direction from which reinforcements are sent.

### 1. Deployment Phase (Placing Forces)

During this phase, players take turns until all players have deployed all of their force cubes.

On your turn, you perform the following actions:

- **Roll Dice**: Roll 3 six-sided dice. You have one chance to reroll, but you must reroll all 3 dice.

- **Allocate Dice**: Divide the results of the 3 dice into two groups: 1 die and 2 dice.

- **Determine Position and Quantity**:
    - The sum of the 2 dice determines the region where you will deploy forces (for example, rolling 3 and 5 means deploying to region "8").
    - The remaining 1 die's value determines the number of forces you deploy this turn (specifically, half the die value, rounded up. For example, rolling 1 or 2 deploys 1 force; rolling 5 or 6 deploys 3 forces).

- **Place Forces**: Place the corresponding number of your force cubes on the region you selected.

When a player exhausts all their force cubes, they receive a priority ranking. The first player to use all their forces gets priority 1, the second gets priority 2, and so on. This order is crucial for tie-breaking in the resolution phase. When all players have exhausted their forces, the deployment phase ends.

### 2. Resolution Phase (Determining Victory)

After the deployment phase ends, the ownership and scoring of each region are calculated.

- **Sequential Resolution**: Starting from the region with the smallest number (2) on the map, resolve regions in order up to the largest (12).

For each region, resolve in the following order:

- **Determine Ownership**: In the current region being resolved, the player with the most force cubes gains control of that region.

- **Tie-Breaking**: If multiple players have the same number of forces and it is the highest, the player with the higher priority ranking (i.e., who finished deploying all forces earlier) wins control of that region.

- **Receive Reinforcements**: This is the game's most critical mechanism! When you win control of a region (have the most forces), you can immediately add **2** of your force cubes as reinforcements to all regions that are **adjacent** to that region, **not yet resolved**, and where **you already have at least 1 force**. Adjacent regions refer to those connected by land or water routes.

- **Scoring**: The region's controller (the player with the most forces) receives points equal to the full region number. The player with the second-most forces receives half the region number (rounded down).

After all regions are resolved, the game ends.

### 3. Victory Condition

After all regions are resolved, each player adds up the points from all regions they control. The player with the highest total score wins!

