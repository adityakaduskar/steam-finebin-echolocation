| agent | target | decoder | memory state h_t | current observation only |
|---|---|---|---|---|
| sonar, fixed click (n=3) | local geometry | linear | 0.790 ± 0.008 | 0.806 ± 0.006 |
| sonar, fixed click (n=3) | local geometry | mlp | 0.803 ± 0.007 | 0.832 ± 0.002 |
| sonar, fixed click (n=3) | visited | linear | 0.755 ± 0.021 | 0.781 ± 0.008 |
| sonar, fixed click (n=3) | visited | mlp | 0.861 ± 0.003 | 0.808 ± 0.007 |
| sonar, fixed click (n=3) | visited, among walkable cells (memory) | linear | 0.677 ± 0.022 | 0.618 ± 0.008 |
| sonar, fixed click (n=3) | visited, among walkable cells (memory) | mlp | 0.762 ± 0.006 | 0.625 ± 0.009 |
| sonar + learned beam (n=3) | local geometry | linear | 0.775 ± 0.014 | 0.749 ± 0.017 |
| sonar + learned beam (n=3) | local geometry | mlp | 0.789 ± 0.016 | 0.779 ± 0.019 |
| sonar + learned beam (n=3) | visited | linear | 0.739 ± 0.024 | 0.714 ± 0.017 |
| sonar + learned beam (n=3) | visited | mlp | 0.840 ± 0.006 | 0.735 ± 0.019 |
| sonar + learned beam (n=3) | visited, among walkable cells (memory) | linear | 0.674 ± 0.015 | 0.582 ± 0.007 |
| sonar + learned beam (n=3) | visited, among walkable cells (memory) | mlp | 0.755 ± 0.010 | 0.579 ± 0.005 |
| head-scan binaural (n=3) | local geometry | linear | 0.754 ± 0.014 | 0.745 ± 0.015 |
| head-scan binaural (n=3) | local geometry | mlp | 0.755 ± 0.016 | 0.761 ± 0.018 |
| head-scan binaural (n=3) | visited | linear | 0.780 ± 0.032 | 0.722 ± 0.014 |
| head-scan binaural (n=3) | visited | mlp | 0.831 ± 0.012 | 0.747 ± 0.013 |
| head-scan binaural (n=3) | visited, among walkable cells (memory) | linear | 0.708 ± 0.023 | 0.575 ± 0.015 |
| head-scan binaural (n=3) | visited, among walkable cells (memory) | mlp | 0.757 ± 0.009 | 0.594 ± 0.011 |
| blind (n=3) | local geometry | linear | 0.611 ± 0.006 | 0.502 ± 0.002 |
| blind (n=3) | local geometry | mlp | 0.614 ± 0.002 | 0.503 ± 0.003 |
| blind (n=3) | visited | linear | 0.774 ± 0.046 | 0.509 ± 0.010 |
| blind (n=3) | visited | mlp | 0.843 ± 0.010 | 0.511 ± 0.010 |
| blind (n=3) | visited, among walkable cells (memory) | linear | 0.763 ± 0.043 | 0.513 ± 0.013 |
| blind (n=3) | visited, among walkable cells (memory) | mlp | 0.830 ± 0.011 | 0.515 ± 0.013 |

Held-out-building AUROC averaged over the 120 non-centre cells of an 11 x 11 egocentric grid (0.5 m); 0.5 = chance.
