# Implementing and automating Ultra Chinese Checkers

[According to Wikipedia](https://en.wikipedia.org/wiki/Chinese_checkers#Fast-paced_or_Super_Chinese_Checkers), the "fast-paced" version of chinese checkers allows one to jump over non-adjacent pieces and is called Super Chinese Checkers. The person who introduced this version to me called the game "Symmetry". I quickly found out that it was more fun to allow one to jump over any symmetrical arrangement of pieces. This version is mentioned in the Wikipedia article as well, but is not named. Based on the aformentioned information, it seems natural to name it either Ultra Chinese Checkers or Supersymmetry.

There are 2 implementations of the game in this repo:

* `web-supersymmetry` has a Javascript-version which is fully playable and has a lot of options for custom rules.
* `python-supersymmetry` is a Python version which is more theory-driven. It is centered around a Jupyter notebook where I explore various algorithms and heuristics for creating bot players.

