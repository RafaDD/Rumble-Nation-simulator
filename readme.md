# Rumble Nation Simulator

[中文说明文档](docs/readme_CN.md)

## Installation

You can install all required dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Alternatively, you can install the dependencies manually:

```bash
pip install PyQt6 numpy torch pandas
```

**Note**: PyTorch installation may require additional steps depending on your system. For GPU support, visit [PyTorch's official website](https://pytorch.org/get-started/locally/) for platform-specific installation instructions.

## Running the Game

To start the game with the graphical user interface, run:

```bash
python play_ui.py
```

This will launch the setup dialog where you can configure your game before starting.

## Game Interface

### Setup Screen

<p align="center">
  <img src="imgs/setup.png" height="400">
</p>

The setup screen allows you to configure game parameters before starting. You can set the number of players, choose AI opponents, configure AI behavior, and customize player names.

### Gameplay Screen

<p align="center">
  <img src="imgs/gameplay.png" height="450">
</p>

The main gameplay interface shows the game map, player information, dice results, and action controls. You can see the current state of all regions, player scores, and available actions.

## Game Configuration Parameters

When you launch the game, you'll be presented with a setup dialog where you can configure the following parameters:

### Model Stage
- **Default**: 0
- **Description**: Determines which version of the AI model to use. Only 0 is available currently.

### Number of Players
- **Default**: 3
- **Description**: Sets the total number of players in the game. This affects the game dynamics, available forces per player, and the AI model selection.

### AI Search Time
- **Default**: 8.0 seconds
- **Description**: Controls how long the AI spends thinking about each move. Higher values generally result in better AI decisions but slower gameplay. Lower values make the AI respond faster but may reduce decision quality.

### Player Configuration
For each player, you can configure:

- **Player Name**: Custom name for the player (defaults to "Player 1", "Player 2", etc.)
- **AI Control**: Checkbox to enable AI control for that player. When enabled, the AI will automatically make decisions for that player. When disabled, the player will be controlled manually by the user.

## Game Rules

For detailed game rules, please refer to:
- [English Rules](docs/rules_EN.md)
- [中文规则](docs/rules.CN.md)
