# Problem

Most 2 player games are either about who can fight better or who knows the controls better,
and the other player is always right in front of you. There arent alot of games where the fun
comes from not knowing where the other person is and having to actually think about it. Hide
and seek type games are fun because you have to guess what the other person is doing, lie to
them, and read the clues they leave behind, but when you play them on one computer it doesnt
work cause both players can just see each others turns. Two Assassins is a 2 player turn based
game where each player is an assassin hiding in a medival town, and they have to find and
expose the other player before they get found themselves, using clues from the townspeople,
disguises and tricks instead of just fighting.

# Initial requirements

- R1. The game creates a medival town made up of locations (ex. market, well, church, tavern,
  blacksmith, gates) that are connected to each other, and fills it with NPCs that move around
  the town on there own. Each player starts in a different random location, far away from each
  other, and is disguised as a townsperson.
- R2. The players take turns on the same computer. Between turns there should be a "pass the
  device" screen so the next player cant see what the last player did. During your turn you can
  only see your own location, your own clues and your own disguise, never where the other
  player is.
- R3. Each turn the player gets a set number of action points (ex. 3) to spend on actions.
  Actions include moving to a connected location, asking an NPC about what they saw, and
  hiding. Different actions cost different amounts of points.
- R4. When a player asks an NPC, the NPC gives a clue about what they saw, but clues should be
  delayed and not always exact (ex. "a hooded figure passed the well 2 turns ago"). So the
  player learns where the other player was, not where they are right now, and has to guess
  where they went.
- R5. Players can also do tricks to mess with the other player. Bribe an NPC so they lie to the
  next person who asks about you, change your disguise so old clues about your clothes are
  useless, and leave a false trail by dropping something in a place you never went.
- R6. When a player thinks they found the other player, they can make an accusation by
  choosing which person in there location is the other player. If they are right they win. If
  they are wrong, the other player gets told where the accuser is.
- R7. The game has a time limit, if nobody wins by dawn (ex. 30 turns) the game ends. The
  player who collected more true clues about the other player wins, and if its tied its a draw.
- R8. At the end of the game the program should show a replay of the whole map, where both
  players went every turn, and which clues were true or lies, so the players can see how close
  they actually were to each other.
