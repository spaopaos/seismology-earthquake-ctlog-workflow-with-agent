# Earthquake Phase Association Using a Bayesian Gaussian Mixture Model

Source: zhu-2022-gamma.pdf
Extraction: pdftotext; physical PDF page numbers, starting at 1.
Text-layer extraction does not reproduce figures and may imperfectly render formulas or tables.

## PDF page 1

RESEARCH ARTICLE

Earthquake Phase Association Using a Bayesian Gaussian
Mixture Model

Special Section:
Machine learning for Solid
Earth observation, modeling and
understanding

Weiqiang Zhu1 , Ian W. McBrearty1, S. Mostafa Mousavi1
Gregory C. Beroza1

10.1029/2021JB023249

Key Points:

• W
 e proposed an new approach
to solve phase association as an
unsupervised clustering problem using
the Bayesian Gaussian Mixture Model
• We used the multivariate Gaussian
distribution to represent both phase
arrival time and amplitude to improve
association
• Our unsupervised method is fast
without the need for conventional
grid-search or supervised training
Supporting Information:

Supporting Information may be found in
the online version of this article.
Correspondence to:

W. Zhu,
zhuwq@stanford.edu
Citation:

Zhu, W., McBrearty, I. W., Mousavi, S.
M., Ellsworth, W. L., & Beroza, G. C.
(2022). Earthquake phase association
using a Bayesian Gaussian Mixture
Model. Journal of Geophysical Research:
Solid Earth, 127, e2021JB023249. https://
doi.org/10.1029/2021JB023249
Received 18 SEP 2021
Accepted 27 MAR 2022
Author Contributions:

Conceptualization: Weiqiang Zhu, Ian
W. McBrearty, S. Mostafa Mousavi,
William L. Ellsworth, Gregory C. Beroza
Data curation: Weiqiang Zhu
Formal analysis: Weiqiang Zhu
Funding acquisition: Gregory C. Beroza
Investigation: Weiqiang Zhu
Methodology: Weiqiang Zhu, Ian W.
McBrearty, S. Mostafa Mousavi, William
L. Ellsworth, Gregory C. Beroza
Project Administration: Gregory C.
Beroza
Resources: Weiqiang Zhu
Software: Weiqiang Zhu

© 2022. American Geophysical Union.
All Rights Reserved.

ZHU ET AL.

, William L. Ellsworth1

, and

Department of Geophysics, Stanford University, Stanford, CA, USA

1

Abstract Earthquake phase association algorithms aggregate picked seismic phases from a network
of seismometers into individual sesimic events and play an important role in earthquake monitoring and
research. Dense seismic networks and improved phase picking methods produce massive seismic phase
datasets, particularly for earthquake swarms and aftershocks occurring closely in time and space, making
phase association a challenging problem. We present a new association method, the Gaussian Mixture Model
Association (GaMMA), that combines the Gaussian mixture model with earthquake location, origin time,
and magnitude estimation. We treat earthquake phase association as an unsupervised clustering problem in a
probabilistic framework, where each earthquake corresponds to a cluster of P and S phases with a hyperbolic
moveout of arrival times and a decay of amplitude with distance. We use the multivariate Gaussian distribution
to model the collection of phase picks of an event; and the mean of the multivariate Gaussian distribution is
given by the predicted arrival time and amplitude from the causative event. We carry out the pick assignment
to each earthquake and determine earthquake source parameters (i.e., earthquake location, origin time,
and magnitude) under the maximum likelihood criterion using the Expectation-Maximization algorithm.
The GaMMA method does not require typical association steps of other algorithms, such as grid-search or
supervised training. The results for both synthetic tests and for the 2019 Ridgecrest earthquake sequence show
that GaMMA effectively associates phases from a temporally and spatially dense earthquake sequence while
producing useful estimates of earthquake location and magnitude.
Plain Language Summary Earthquakes are monitored by seismic networks consisting of several
to hundreds of seismometers. An earthquake detection workflow usually has two important steps: detecting/
picking seismic phases at each seismometer and associating picked phases across multiple seismometers in
a network. Deep-learning-based phase pickers have greatly improved phase detection performance and can
automatically generate many more seismic phases than conventional algorithms. These massive numbers
of automatic phase picks pose a challenge for the phase association task. We have developed a new phase
association method using a Bayesian Gaussian Mixture Model. We treat the phase association problem as a
unsupervised clustering problem meaning that we aim to cluster detected phases into different groups based
on individual earthquakes that produce these phases. The Gaussian mixture model makes it easy to consider
multiple phase parameters, such as phase arrival time, phase amplitude, phase picking quality score, and
phase type, to improve phase association. We test our method on both synthetic data and the 2019 Ridgecrest
earthquake. The results show that our method can effectively associate phases from a temporally and spatially
dense earthquake sequence and generate a more complete earthquake catalog than catalogs created using
conventional methods.
1. Introduction
Earthquake catalogs are fundamental products that are widely used in seismology to study and model various aspects of seismicity. Extensive efforts have been made to generate more complete catalogs with many
more smaller earthquakes and more precise location and magnitude estimates. These high-resolution high-precision catalogs have the potential to reveal relationships among earthquakes and illuminate active structures that
would otherwise remain hidden (Beroza et al., 2021; Hauksson et al., 2012; Park et al., 2020; Ross, Trugman,
et al., 2019; Tan et al., 2021; Waldhauser & Schaff, 2008; Yoon et al., 2015). A standard earthquake-monitoring
workflow from seismic waveforms to earthquake catalogs includes several tasks, including: phase detection and
picking (Allen, 1978), phase association (Yeck et al., 2019), earthquake location (Klein, 2002), and magnitude
estimation (Richter, 1935).
1 of 15

## PDF page 2

Supervision: William L. Ellsworth,
Gregory C. Beroza
Validation: Weiqiang Zhu, Gregory C.
Beroza
Visualization: Weiqiang Zhu
Writing – original draft: Weiqiang Zhu
Writing – review & editing: Weiqiang
Zhu, Ian W. McBrearty, S. Mostafa
Mousavi, William L. Ellsworth, Gregory
C. Beroza

10.1029/2021JB023249

The phase picking step detects seismic phases such as P-wave and S-wave phases at each seismic station. The
phase association step aggregates these phases from multiple stations of a seismic network into separate groups
associated with each earthquake. Earthquake location and magnitude are then estimated from the associated
phase information such as arrival time and amplitude. The resulting catalog can be further enhanced through
template matching (Gibbons & Ringdal, 2006; Peng & Zhao, 2009; Shelly et al., 2007) or subspace projection
(Barrett & Beroza, 2014; Harris & Dodge, 2011) that use the detected earthquakes as templates to re-scan the
waveforms and detect small earthquakes with similar waveforms.
The phase picking step has been significantly improved by deep-learning-based pickers that learn from manual
picks labeled by analysts to detect millions of phase picks from raw seismic waveforms (Mousavi et al., 2020;
Ross et al., 2018; W. Zhu & Beroza, 2018). The rapidly growing volume of automatic picks and the ongoing
growth of seismic networks makes developing effective phase association methods crucial; yet, phase association has not received the attention that has been devoted to other earthquake monitoring tasks. Association
methods based on back-projection are most commonly used in classic earthquake monitoring systems such
as Hydra (Patton et al., 2016), Earthworm (Friberg et al., 2010), and SeisComP3 (Weber et al., 2007). These
approaches usually deploy a grid-search, and back-project phase picks based on the expected moveout with
distance. An earthquake and its initial location is declared based on the number of phase picks inside a spatial
grid. Although back-projection-based association is robust and effective, its performance is limited for dense
earthquake sequences when earthquakes occur so closely in time and space that interpreting the maxima resulting
from back-projection becomes problematic. Studies have continued to focus on improving the grid-search and
back-projection approach for different scenarios (Arora et al., 2013; Draelos et al., 2015; Gibbons et al., 2016;
Zhang et al., 2019). Specifically, both Net-VISA (Arora et al., 2013) and PEDAL (Draelos et al., 2015) incorporated a probabilistic framework to add prior information from historical catalogs and consider the uncertainty
of phase picks, velocity models, and grid sizes. These methods rely on a complex combination of probabilistic
models and many hyper-parameters that control performance and accuracy. Several new approaches have been
proposed to solve the earthquake phase association using: graph theory (McBrearty, Gomberg, et al., 2019),
the RANSAC algorithm (L. Zhu et al., 2021; Woollam et al., 2020), and deep learning (Dickey et al., 2020;
McBrearty, Delorey, & Johnson, 2019; Ross, Yue, et al., 2019). When combined with the rapid development of
phase picking methods, better association methods have the potential to improve significantly the overall performance of earthquake monitoring pipelines.
We propose an association method based on a Bayesian Gaussian Mixture Model (GMM), which is an unsupervised machine learning method for clustering (Bishop, 2006) that has been widely used in different research
fields, such as image processing (Permuter et al., 2006), speech recognition (Reynolds & Rose, 1995), and
earthquake studies (Ross et al., 2020; Seydoux et al., 2020). Earthquake phase association can be treated as an
unsupervised clustering problem, with groups of phase picks, in time and space, arising from a discrete set of
earthquake origins. We combine the GMM with earthquake location, origin time, and magnitude estimation,
so that the new Gaussian Mixture Model Association (GaMMA) method can cluster phase picks based on the
physical constraints of arrival time moveout and amplitude decay with distance. Phase amplitude information is
often neglected because it can be difficult to account in conventional association approaches; however, GaMMA
is designed such that it can use phase arrival time, phase-type identification, and amplitude information for
association while simultaneously estimating the underlying event source characteristics (i.e., location and magnitude). Moreover, GaMMA does not require extra association steps of grid-search or supervised training. These
attributes make GaMMA an appealing approach to address the challenges arising in processing large numbers of
automatic picks in earthquake monitoring workflows.

2. Method
The objective of earthquake phase association is to post-process a large collection of phases picked on individual
seismic stations and cluster them into groups of seismic phases originating from a common earthquake event, so
that subsequent earthquake characterization tasks can be performed on individual events. Arrival times of P and S
phases from the same earthquake follow a hyperbolic moveout that is determined by the hypocentral distance and
the Earth model (i.e., seismic wave speed). This moveout allows association algorithms to distinguish between
phases from different earthquakes. In this work, we extend the association problem by using both phase arrival
time and phase amplitude information. On average, the phase amplitude scales with earthquake magnitude and
ZHU ET AL.

2 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 3

10.1029/2021JB023249

decays with hypocentral distance. Thus, amplitude provides additional information to improve phase association. We formulate the association problem
as follows: Given N seismic phases (xi, yi, zi, ti, ai), that is, arrival time ti
and amplitude ai recored at the ith seismic station located at (xi, yi, zi), we
seek to group these phases into K earthquakes and estimate the underlying
source parameters (xk, yk, zk, tk, mk), that is, location (xk, yk, zk), origin time tk,
and magnitude mk of the kth earthquake. We solve this association problem
using the GMM (Permuter et al., 2006), which is an unsupervised clustering
method that groups N data points into K clusters by maximizing the probability that these N data can be explained by a mixture of K Gaussian distributions. We incorporate the physical constraints on phase arrival time and
amplitude into the GMM to make it suitable for our association problem.
Figure 1 illustrates how we model the Gaussian distributions to calculate
the probability of the sequence of phases generated by two causative earthquakes. The mathematical details are explained in the following sections.
Figure 1. Gaussian mixture model for association. We model Gaussian
distributions based on the theoretical phase arrival times and amplitudes as
shown by the dashed lines from the two earthquakes (two crosses) in the
figure, so that the probability of each pick is determined by the difference
from the theoretical arrival time and amplitude. The phase association task,
which is to estimate maximum likelihood of these picks, can be solved by the
Expectation-Maximization (EM) algorithm. The EM iteration converges to
the correct phase clustering for each earthquake and estimates its approximate
source parameters. Note that we use both phase arrival time and phase
amplitude information for phase association. For simplicity, only the time axis
and a generalized distance from the edge are plotted.

2.1. Bayesian Gaussian Mixture Model
We cast the association problem in a probabilistic framework where we use a
mixture of Gaussian distributions to model the probability of each phase pick
generated by a mixture of earthquake sources:
𝐾𝐾
∑
(
)
𝑝𝑝 (𝐱𝐱𝑖𝑖 ) = 𝑤𝑤𝑖𝑖
𝜙𝜙𝑘𝑘  𝐱𝐱𝑖𝑖 |𝜇𝜇𝑘𝑘 , 𝚲𝚲−1
(1)
𝑘𝑘
𝑘𝑘=1

)
(
(
)
1
1
𝑇𝑇
1∕2
|𝚲𝚲
|
exp
−
−
𝜇𝜇
𝚲𝚲
−
𝜇𝜇
 𝐱𝐱𝑖𝑖 |𝜇𝜇𝑘𝑘 , 𝚲𝚲−1
=
)
(𝐱𝐱
)
(𝐱𝐱
𝑘𝑘
𝐢𝐢
𝑘𝑘
𝑘𝑘
𝐢𝐢
𝑘𝑘
(2)
𝑘𝑘
2
(2𝜋𝜋)𝑛𝑛∕2

𝐾𝐾
∑
𝜙𝜙𝑘𝑘 = 1
(3)
𝑘𝑘=1

where xi represents a phase pick including arrival time and amplitude (ti, ai) values at the ith station. ϕk is the
mixture component coefficient of the kth earthquake.
𝐴𝐴
 represents a Gaussian distribution, with μk as its mean.
(
)
μk represents the theoretical phase arrival time and amplitude
𝐴𝐴
𝑡𝑡̂𝑖𝑖𝑖𝑖 , 𝑎𝑎̂𝑖𝑖𝑖𝑖 for each ith station determined by the kth
earthquake. Λk is the precision (inverse covariance) matrix of the Gaussian distribution. wi is the phase picking
quality score between [0, 1]. n is the number of feature dimensions, which is one if only time information is used
or two if both time and amplitude information are used. Based on the Gaussian mixture distribution, we can
calculate the probability of a set of recorded phases (x1, x2, …, xN) being generated by a mixture
𝐴𝐴 of 𝐴𝐴 events. If
we assume these observations are independent and identically distributed (i.i.d.), then the log likelihood function
is given by:
)
(
𝐾𝐾
𝑁𝑁
∑
∑
(
)
−1
log (𝑝𝑝(𝐗𝐗|𝜙𝜙𝜙 𝜙𝜙𝜙 𝚲𝚲)) =
log 𝑤𝑤𝑖𝑖
𝜙𝜙𝑘𝑘  𝐱𝐱𝑖𝑖 |𝜇𝜇𝑘𝑘 , 𝚲𝚲𝑘𝑘
(4)
𝑖𝑖=1

𝑘𝑘=1

we find the assignment from N phase picks to K earthquakes, which is the goal of association, and the corresponding earthquake source parameters by maximizing the log likelihood of Equation 4.

𝐴𝐴

ZHU ET AL.

A limitation of the GMM formulation is that we need to assume the number of underlying earthquakes K. To
address this unknown, we implement the Bayesian GMM (Bishop, 2006), which uses variational inference
to calculate approximate posterior distributions for the parameters of a Gaussian mixture distribution. Three
conjugate priors are introduced. In particular, we use a Dirichlet prior for the mixture component coefficient,
𝐴𝐴(𝜙𝜙) =  (𝛼𝛼0 ) where α0 is the weight concentration prior (Ferguson, 1973), which controls the concentration of
(
)
mixture components; a Gaussian prior for the mean conditioned on the precision,
𝐴𝐴
𝐴𝐴 (𝜇𝜇𝑘𝑘 |Λ𝑘𝑘 ) =  𝜇𝜇0 , (𝛽𝛽0 Λ𝑘𝑘 )−1
where μ0 is the prior on the mean and β0 is the precision prior on the mean; and a Wishart prior for the precision
Λk, p (Λk) = W(W0, ν0) where W0 is the covariance prior and ν0 is the degrees of freedom prior (Wishart, 1928),
3 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 4

10.1029/2021JB023249

which controls the estimation of covariance. The Bayesian model penalizes parameters that are away from the
priors, which balances data fitting and model complexity. The mixture components (i.e., earthquakes) that do
not contribute to explaining the data will have approximately zero mixture coefficients, so that we can choose a
large number of components in the mixture model without over-fitting. In practice, we can initialize the space
with many redundant earthquake hypocenters, and the Bayesian GMM suppresses unnecessary sources to infer
an accurate number of earthquakes with associated picks.
2.2. Expectation-Maximization (EM) Algorithm
We use the the EM algorithm to solve for the maximum likelihood estimate of p(x) (Equation 4). To consider
physical constraints on phase arrival time and amplitude for association, we incorporate the estimate of earthquake location, origin time, and magnitude into the EM algorithm. We then iteratively update the assignments
from picks to earthquakes in the E-step and optimize the earthquake parameters in the M-step:
2.2.1. E-Step
𝜙𝜙𝑘𝑘  (𝐱𝐱𝑖𝑖 |𝜇𝜇𝑘𝑘 , 𝚺𝚺𝑘𝑘 )
𝛾𝛾𝑖𝑖𝑖𝑖 = ∑𝐾𝐾
(5)
𝑘𝑘=1 𝜙𝜙𝑘𝑘  (𝐱𝐱𝑖𝑖 |𝜇𝜇𝑘𝑘 , 𝚺𝚺𝑘𝑘 )

where γik is the probability that phase pick xi (arrival time ti and wave amplitude ai) is generated by the kth
earthquake.
2.2.2. M-Step
1.	Effective number of picks assigned to the k-th earthquake
𝑁𝑁
∑
𝑁𝑁𝑘𝑘 =
𝛾𝛾𝑖𝑖𝑖𝑖
(6)
𝑖𝑖=1

𝑁𝑁
𝜙𝜙𝑘𝑘 = 𝑘𝑘
(7)
𝑁𝑁

2.	Earthquake location, origin time, and magnitude of the k-th earthquake
𝑁𝑁
∑
(
)
minimize𝑙𝑙 (𝑥𝑥𝑘𝑘 , 𝑦𝑦𝑘𝑘 , 𝑧𝑧𝑘𝑘 , 𝑡𝑡𝑘𝑘 ) =
𝛾𝛾𝑖𝑖𝑖𝑖  𝑡𝑡𝑖𝑖 , 𝑡𝑡̂𝑖𝑖𝑖𝑖 (𝑥𝑥𝑘𝑘 , 𝑦𝑦𝑘𝑘 , 𝑧𝑧𝑘𝑘 , 𝑡𝑡𝑘𝑘 )
(8)
(𝑥𝑥𝑘𝑘 ,𝑦𝑦𝑘𝑘 ,𝑧𝑧𝑘𝑘 ,𝑡𝑡𝑘𝑘 )
𝑖𝑖=1
𝑁𝑁
1 ∑
𝛾𝛾𝑖𝑖𝑖𝑖 𝑎𝑎′ (𝑎𝑎𝑖𝑖 , 𝑑𝑑𝑖𝑖𝑖𝑖 )
𝑚𝑚𝑘𝑘 =
(9)
𝑁𝑁𝑘𝑘 𝑖𝑖=1

3.	Theoretical arrival time, amplitude, and statistics of residuals
⎡ 𝑡𝑡̂𝑖𝑖𝑖𝑖 ⎤ ⎡ 𝑡𝑡 (𝑥𝑥𝑘𝑘 , 𝑦𝑦𝑘𝑘 , 𝑧𝑧𝑘𝑘 , 𝑡𝑡𝑘𝑘 ) ⎤
⎥
⎥=⎢
𝜇𝜇𝑘𝑘 = ⎢
(10)
⎥
⎢ 𝑎𝑎̂ ⎥ ⎢
𝑎𝑎 (𝑚𝑚𝑘𝑘 , 𝑑𝑑𝑖𝑖𝑖𝑖 )
⎣ 𝑖𝑖𝑖𝑖 ⎦ ⎣
⎦
𝑁𝑁
1 ∑
𝛾𝛾𝑖𝑖𝑖𝑖 (𝐱𝐱𝑖𝑖 − 𝜇𝜇𝑘𝑘 ) (𝐱𝐱𝑖𝑖 − 𝜇𝜇𝑘𝑘 )𝑇𝑇
𝚲𝚲−1
(11)
𝑘𝑘 =
𝑁𝑁𝑘𝑘 𝑖𝑖=1

where  is a loss function of the absolute residuals between the picked phase arrival times ti and the theoretical
𝐴𝐴
arrival𝐴𝐴times 𝑡𝑡̂𝑖𝑖𝑖𝑖 from the kth earthquake. Minimization of the loss function l gives an estimate of the earthquake
location and origin time (xk, yk, zk, tk). mk is the magnitude of the kth earthquake.
𝐴𝐴
𝑡𝑡 represents the function used to
calculate theoretical phase arrival𝐴𝐴time
𝐴𝐴 𝑡𝑡̂𝑖𝑖𝑖𝑖 . 𝑎𝑎 represents the function to calculate theoretical phase amplitude
𝐴𝐴
𝐴𝐴𝐴𝑖𝑖𝑖𝑖
based on earthquake magnitude m𝐴𝐴k, and 𝑎𝑎′ represents the function to estimate earthquake magnitude using phase
amplitude. dik is the distance from the kth earthquake to ith seismic station. Here we decouple the optimization of

ZHU ET AL.

4 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 5

10.1029/2021JB023249

earthquake magnitude (Equation 9) from the optimization of earthquake location and time (Equation 8). We use
arrival times to constrain earthquake location and use phase amplitudes to constrain earthquake magnitude. Note
that although we decouple the two optimizations, the precision matrix (Equation 11) considers the correlation
between arrival time and amplitude residuals. In this way, both arrival time and amplitude information are used
for the association process of clustering picks among earthquakes (Equation 5).
For the Bayesian GMM, we add another stage in the M-step to update the posterior parameters:
𝛼𝛼𝑘𝑘 = 𝛼𝛼0 + 𝑁𝑁𝑘𝑘
(12)
𝛽𝛽𝑘𝑘 = 𝛽𝛽0 + 𝑁𝑁𝑘𝑘
(13)
1
𝐦𝐦𝑘𝑘 =
(𝛽𝛽0 𝐦𝐦0 + 𝑁𝑁𝑘𝑘 𝜇𝜇𝑘𝑘 )
(14)
𝛽𝛽𝑘𝑘
𝛽𝛽0 𝑁𝑁𝑘𝑘
−1
−1
𝐖𝐖−1
(𝜇𝜇𝑘𝑘 − 𝐦𝐦0 ) (𝜇𝜇𝑘𝑘 − 𝐦𝐦0 )T
(15)
𝑘𝑘 = 𝐖𝐖0 + 𝑁𝑁𝑘𝑘 𝚲𝚲𝑘𝑘 +
𝛽𝛽0 + 𝑁𝑁𝑘𝑘
𝜈𝜈𝑘𝑘 = 𝜈𝜈0 + 𝑁𝑁𝑘𝑘
(16)

The E-step is modified as:
}
{
𝐾𝐾
∑
𝜈𝜈𝑘𝑘
𝐷𝐷
1∕2
T
̃
,
−
−
𝐦𝐦
𝐖𝐖
−
𝐦𝐦
𝛾𝛾𝑖𝑖𝑖𝑖 = 1
𝛾𝛾
∝
𝜋𝜋
̃
exp
−
Λ
)
(𝐱𝐱
)
(𝐱𝐱
(17)
𝑛𝑛
𝑘𝑘
𝑘𝑘
𝑛𝑛
𝑘𝑘
𝑖𝑖𝑖𝑖
𝑘𝑘 𝑘𝑘
2𝛽𝛽𝑘𝑘
2
𝑘𝑘=1
)
(
𝐷𝐷
∑
𝜈𝜈𝑘𝑘 + 1 − 𝑖𝑖
̃ 𝑘𝑘 =
+ 𝐷𝐷 ln 2 + ln |𝐖𝐖𝑘𝑘 |
ln Λ
𝜓𝜓
(18)
2
𝑖𝑖=1
( )
ln 𝜋𝜋̃𝑘𝑘 = 𝜓𝜓 (𝛼𝛼𝑘𝑘 ) − 𝜓𝜓 𝛼𝛼
̂
(19)
∑
where 𝐴𝐴
𝐴𝐴
𝐴 = 𝑘𝑘 𝛼𝛼𝑘𝑘 and ψ is the digamma function (Abramowitz & Stegun, 1964). The explanation of these updating rules is detailed in Bishop (2006)'s textbook.

2.3. Earthquake Location and Magnitude Estimation
The iteration of the EM algorithm updates the clustering of picks based on earthquakes and optimizes the corresponding earthquake source parameters. We focus on efficient association rather than accuracy of earthquake
source parameters, which can be realized once phases are properly associated, so we choose two basic approaches
to estimate approximate earthquake locations and magnitudes. We optimize Equation 8 with a Huber loss function (Huber, 1992) as the target to reduce the effect of outliers:
)2
⎧1(
for |𝑡𝑡 − 𝑡𝑡̂| ≤ 𝛿𝛿
(
) ⎪ 𝑡𝑡 − 𝑡𝑡̂
𝛿𝛿 𝑡𝑡 − 𝑡𝑡̂ = ⎨ 2 (
)
(20)
1
⎪𝛿𝛿 |𝑡𝑡 − 𝑡𝑡̂| − 𝛿𝛿 ,
otherwise.
⎩
2

where the hyper-parameter δ is set to 1s in this test. For this proof-of-concept study, we use a uniform velocity
model to calculate the theoretical phase arrival time:
̂𝑡𝑡𝑖𝑖𝑖𝑖 (𝑥𝑥𝑘𝑘 , 𝑦𝑦𝑘𝑘 , 𝑧𝑧𝑘𝑘 , 𝑡𝑡𝑘𝑘 ) = 𝑡𝑡 (𝑥𝑥𝑘𝑘 , 𝑦𝑦𝑘𝑘 , 𝑧𝑧𝑘𝑘 , 𝑡𝑡𝑘𝑘 ) = 𝑑𝑑𝑖𝑖𝑖𝑖 + 𝑡𝑡𝑘𝑘
(21)
𝑣𝑣

we then solve the minimization of Equation 8 using the BFGS algorithm (Fletcher, 2013). Advanced earthquake
location algorithms and complex velocity models can also be applied to solving Equation 8 but at a higher computational cost.
To estimate earthquake magnitude in Equation 9, we use a linear relationship between the logarithm of the phase
amplitude and earthquake magnitude:
𝑚𝑚
̂ 𝑖𝑖𝑖𝑖 = 𝑎𝑎′ (𝑎𝑎𝑖𝑖 , 𝑑𝑑𝑖𝑖𝑖𝑖 ) = 𝑐𝑐0 + 𝑐𝑐1 log 𝑎𝑎𝑖𝑖 + 𝑐𝑐2 log 𝑑𝑑𝑖𝑖𝑖𝑖
(22)

ZHU ET AL.

5 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 6

10.1029/2021JB023249

Station correction terms can be added to consider site effects, such as site amplification factors (Münchmeyer
et al., 2020). Based on the measured phase amplitude type, for example, displacement, peak ground velocity
(PGV), or peak ground acceleration, we can choose from among the Richter empirical magnitude relationship
(Richter, 1935), the Richter simulation-based prediction (Al-Ismail et al., 2020), or ground motion prediction
equations (GMPE) (Picozzi et al., 2018) for Equation 22.

3. Results
We demonstrate the performance of GaMMA first on two synthetic examples and then on six days of data from
the 2019 Ridgecrest, California earthquake sequence.
3.1. Synthetic Test
We created two synthetic experiments to demonstrate the association results of GaMMA. In the first 1D synthetic
experiment, we generated a sequence of both P- and S-phases from six earthquake events. To model the errors
that exist in real data, we added a 0.5s random error in the phase arrival times and scaled the phase amplitude
(PGV) by a random factor between 0.3 and 3. We further added 30% false positive picks at random times. In total,
178 P- and S-phase picks from 40 stations were used for association (left panels of Figure 2). We used a simplified ground motion prediction equation of PGV from Picozzi et al. (2018)'s work: log PGV = −2.175–1.68 log
R + 0.93 M, where R is hypocentral distance and M is earthquake magnitude. The ground truth result is shown
in the middle panels of Figure 2. The symbol size represents the relative size of the phase amplitude and the
earthquake magnitude. We conducted two association tests, using in the first test only the arrival time information (Figure 2a), and in the second test both the arrival time and amplitude information (Figure 2b). The same
parameters and initialization were used for both cases. We initialized the earthquake locations at the center of the
research area and uniformly distributed the earthquake origin times. The association results are shown in the right
panels of Figure 2. At least five of the six true earthquakes are successfully associated in both tests. However,
the sixth event in the lower right corner of Figures 2a and 2b [ii] (marked in brown) is successfully associated
only when amplitudes are used in conjunction with arrival times (Figure 2b [iii]). Without amplitudes (Figure 2a
[iii]) we find multiple incorrect event associations marked by colors pink and purple. This occurs because the
P-phases of this event have arrival times that overlap with another distant event's moveout (the event marked in
red) and are mistakenly associated with this distant event. The extra information provided by amplitude adds the
necessary extra constraint on distance, in addition to time, that allows the sixth event to be associated correctly.
The test with amplitude information also correctly estimates the earthquake magnitudes. This synthetic experiment demonstrates that GaMMA benefits from using both the time and amplitude information in the association
process.
In the second synthetic experiment, we used the station locations of the 2019 Ridgecrest earthquake sequence
and randomly sampled event locations to quantify the association performance of GaMMA. The station locations and the 50 event locations are shown in Figure S1 in Supporting Information S1. We also calculated the
performance of another association method REAL (Zhang et al., 2019) for comparison. We first analyzed the
association speed of GaMMA (Figure 3). Because GaMMA is based on the GMM and does not perform a
grid-search, its computational time scales only with the number of picks times the number of events, while
the computational time of REAL scales with the number of picks times the number of grid points used. In
this test, REAL uses a total of 18,491 (41 × 41 × 11) grid points to achieve a spatial resolution of 3 km and a
depth resolution of 2 km. As a result, GaMMA has a faster association speed than REAL. We then analyzed
the association accuracy of GaMMA. We generated synthetic datasets by adding random Gaussian errors in
phase time and amplitude measurements, false positive picks, and biased velocity models of P and S waves. The
default standard deviations of Gaussian random errors in this test are 0.4s for phase time and 0.4 (log10 m/s) for
phase amplitude in a log scale; the default ratio of false positive picks is 37.5%; and the biased velocity model
is 90% of the true velocity model. The average origin time intervals of the 50 synthetic events are around 10s
or 5s. The association performance of REAL, GaMMA, and GaMMA using only time information are summarized in Table 1. Here, we define the associated event that is within 3s and 15 km from the true event as true
positive association to calculate precision, recall, and F1-score (Powers, 2020). Under this idealized synthetic
setting, both REAL and GaMMA can associate these events successfully. GaMMA using only time information
ZHU ET AL.

6 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 7

10.1029/2021JB023249

Figure 2. Synthetic example: (a) association using only time; (b) association using both time and amplitude. The left panels plot the P- and S-phase picks that scatter
along the time axis and the distance from the edge of the region. The middle panels are plots of the ground truth association result. Unassociated false positives are
plotted in gray. The circle size represents phase amplitude and the cross size represents earthquake magnitude. The right panels show the association results of the
GaMMA method. Note that some phases in the lower right corner of panel (a) [iii] are mis-associated with another distant earthquake marked in red, because these
phases can fit the moveout of both events. Amplitude information provides an extra constraint in distance that resolves this ambiguity as shown in panel (b) [iii].

has similar F1 scores as REAL, while GaMMA using both time and amplitude information achieves a better
association result. In addition to these default values, we further conducted a sensitivity analysis of these three
types of errors to analyze how GaMMA's association performance deteriorates with increasing errors (Figure
S2–S4 in Supporting Information S1). For Gaussian random errors in phase measurements, GaMMA automatically adjusts the estimated covariance matrix (Equation 11), so that the estimated σ11 of phase time and σ22 of
phase amplitude fall around the errors in the data (Figure S2 in Supporting Information S1). The association
performance can be significantly impacted by false positive picks, which can lead to more false associations and
low precision (Figure S3 in Supporting Information S1), and biased velocity models, which can cause systematic biases in theoretical phase times (Figure S4 in Supporting Information S1). Note that the errors in real data
are much more complicated than our synthetic tests and may not follow a Gaussian distribution. This synthetic
test is designed to compare the performance of GaMMA with REAL under the same setting and to analyze
sensitivity under controlled error levels.
ZHU ET AL.

7 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 8

10.1029/2021JB023249

3.2. Test on the 2019 Ridgecrest Earthquake Sequence

Figure 3. Comparison of association speed between REAL and GaMMA.

We next applied GaMMA to part of the 2019 Ridgecrest earthquake sequence
to evaluate its performance on real data. We focused on the initial 6 days of
the sequence when a large number of earthquakes occurred and migrated
from the southwest-striking fault to the northwest-striking fault. We applied
the PhaseNet model (W. Zhu & Beroza, 2018) to extract picks from waveforms of “HH,” “BH,” “EH,” and “HN” channels of 23 stations of the “CI”
network within 1 degree of the location (−117.504 W, 35.705 N). We measured the PGV value over a 8s window after the phase arrival time. We then
associated the detected 651,994 P-picks and 686,291 S-picks using GaMMA.
We used a uniform velocity model with vp = 6 km/s and vs = vp/1.73 for earthquake location estimation and a simple ground motion prediction equation as
above for earthquake magnitude estimation. Because we used such a simple
moveout behavior, we do not expect the earthquake locations to be accurate,
but they are close enough for successful association given the relatively short
source-receiver distances involved.

Figure 4 shows the statistics of the 24,327 associated earthquakes from 496,934 P-picks and 508,454 S-picks,
leaving 155,060 P-picks and 177,837 S-picks unassociated. We also plot the 10,151 earthquakes in the SCSN
catalog (SCEDC, 2013) for comparison. Both the associated earthquake locations and magnitudes agree with
the SCSN catalog (Figures 4b and 4c). Figure 5 shows an association example with a dense sequence of picks
occurring during a 6-min period. GaMMA associates 24 events during this period, while there are only 2
events in the SCSN catalog and 20 events in Ross, Idini, et al. (2019)'s template matching catalog. Figure 8
shows seismic waveforms of six newly detected events in Figure 5. We can see clear earthquake signals in these
examples. These signals are relatively weak and can only be detected at a few stations. Figure 6 shows the
residual distributions of the associated earthquake location and magnitude compared with the SCSN catalog.
The statistics of mean, standard deviation (STD), and median absolute error (MAE) can be found in Table 2.
The covariance matrix in Figure 6d shows that most of the associated earthquakes have small residuals of phase
arrival time and amplitude, indicating that the phase picks match well with the theoretical values determined
by the causative earthquakes found by association. These location and magnitude estimates can be further
improved through the application of established earthquake location and magnitude algorithms once the picks
have been associated.

Table 1
Comparison of Association Results Between REAL and GaMMA

ZHU ET AL.

8 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 9

10.1029/2021JB023249

Figure 4. Association results of the Ridgecrest dataset: (a) associated earthquake frequency, (b) associated earthquake magnitude, (c) associated earthquake location.
Note that because we use a uniform velocity model during association, we do not expect the earthquake locations to be accurate, but they are close enough for effective
association.

We compared the catalog generated by GaMMA with three state-of-art catalogs (Liu et al., 2020; Ross, Idini,
et al., 2019; Shelly, 2020). Table 3 shows the earthquake numbers in these catalogs during the same period. In
each of these cases we assumed these catalogs as ground truth and analyzed whether the earthquakes they contain
are also detected in GaMMA's catalog within a 5s window. Based on the recall rate, more than 90% of earthquakes in the catalogs of SCSN, Liu et al. (2020), and Shelly (2020) are successfully associated by GaMMA.
The low precision and F1-score are due to the large number of new earthquakes associated by GaMMA. To
verify whether these new earthquakes are reasonable, we compared the magnitude distributions of the four catalogs (Figure 7). Most of these new earthquakes associated by GaMMA have a small magnitude and follow the
Gutenberg–Richter magnitude-frequency relationship (Gutenberg, 1956),
which suggests that they may be legitimate detections of real earthquakes.
Table 2
Since we used a simple GMPE (Picozzi et al., 2018) to estimate earthquake
Statistics of Residual Distributions in Figure 6
magnitude based on PGV, we also see discrepancies at the high end of
Error
Δx (km)
Δy (km)
Δz (km)
Δt (s)
Δm
magnitude. The magnitude errors in Figure 6d indicates an underestimation of events above M5. Note that the associated earthquake numbers of
Mean
−0.66
0.53
5.81
−0.37
−0.06
these catalogs are dependent on the hyper-parameters used. For example, we
STD
2.55
2.21
4.15
0.91
0.23
applied two filtering criteria to remove low-quality associations: a minimum
MAE
2.03
1.64
6.35
0.68
0.15
of 15 picks per event, σ11 < 2.0 s and σ22 < 1.0 (log10 m/s). Because of the
ZHU ET AL.

9 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 10

10.1029/2021JB023249

Figure 5. An example of association results from a dense sequence of phase picks starting at time 2019-07-08T00:00:00 (UTC). GaMMA associates 24 events during
this period, while there are only 2 events in the SCSN catalog and 20 events in Ross, Idini, et al. (2019)'s template matching catalog.

unknown ground truth and the trade-off between the number of predictions and the false positives, it is challenging to evaluate the false positive associations in these catalogs.

4. Discussion
The GMM is an effective and widely used unsupervised learning method for clustering. We have combined the
GMM with earthquake location and magnitude estimation to develop a novel GMM-based association method
(GaMMA). We treat earthquake phase association as a clustering problem that aims to cluster phases based on
the causative earthquakes. There are several advantageous features to approaching the phase association task as
an unsupervised clustering problem. First, GaMMA optimizes the association result in a probabilistic framework,
so that GaMMA can flexibly consider phase arrival time, phase amplitude, phase type, and pick quality in association and estimates the covariance of time and amplitude residuals. While it is difficult for conventional association methods to consider phase amplitude information, GaMMA can easily include phase amplitude information both to improve association and to estimate earthquake magnitude. We can further add other useful information,
such as back-azimuths, event duration, and S-P time lags, to the multi-variate Gaussian distribution (Equation 2)
as extra constraints for association. Second, GaMMA does not require grid-search or training commonly used
in other association methods. Supervised training methods could have poor generalization when applied to new
regions with different station geometries and velocity models. Conventional grid-search methods require determining the grid size as an important hyper-parameter. A small grid size can scatter picks of a single earthquake
into multiple grids; and the computational cost grows exponentially as grid size decreases; while a large grid
size can associate multiple false-positive picks or picks from multiple earthquakes into the same grid leading to
false associations. Last, in addition to processing archived seismic datasets, we can apply GaMMA in a real-time
environment using a sliding window and associate picks inside the sliding window. The sliding window approach
involves repeated associations of picks that remain in the sliding window, but because GaMMA is very efficient
for short sequence data, the computational cost is not high. These strengths of GaMMA make it a promising
approach for improved earthquake phase association, and hence improved earthquake monitoring in general.
We note that there are several limitations of GaMMA that need to be considered. First, the time complexity
of the GMM scales with O(K ⋅ N), where K is the number of clusters (earthquakes) and N is the number of
samples (phase picks), so the computational cost could become prohibitive for a long earthquake sequence. In

ZHU ET AL.

10 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 11

10.1029/2021JB023249

Figure 6. Residuals of (a) associated earthquake spatial location, (b) origin time, (c) depth, and (d) magnitude compared with the SCSN catalog. (e) The components
of the covariance matrix of arrival time and amplitude residuals estimated by GaMMA.

practice, however, it is straightforward and effective to segment a long sequence into relatively shorter windows
to improve the association speed by processing data in parallel, as phases that are separated by a certain time
interval (depending on the source-receiver distance) cannot come from a single earthquake. In this work, we
used the DBSCAN algorithm (Schubert et al., 2017) to divide picks into sub-windows for association. Second,
the clustering results of the GMM are affected by the initialization state. In this work, we used a simple
strategy to initialize the earthquake locations uniformly in time. The number of initialized earthquakes is
proportional to an approximated number of earthquakes that is estimated by the number of phase picks divided
by the number of stations. We define the ratio between initialized number and the approximated number of
earthquakes as the oversampling ratio. The effect of this hyper-parameter is analyzed in Figure S5 in Supporting Information S1. Because we use a Bayesian GMM, we can use a larger number of initial clusters (i.e.,
earthquakes) for association. This simple strategy worked well in the experiments described above. Improving initialization strategies has the potential to improve the association performance further. Third, GaMMA
ensures that one pick is only assigned to one earthquake, while conventional back-projection methods may
attribute one pick to several earthquakes. But GaMMA does not consider station-based constraints, such as that
ZHU ET AL.

11 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 12

10.1029/2021JB023249

Figure 7. Comparison of earthquake magnitude distributions.

Figure 8. Waveforms of six newly detected events that are not Ross, Idini, et al. (2019)'s template matching catalog in Figure 5. M is the associated earthquake
magnitude. σ11 and σ22 are the STD of associated phase time and phase amplitude respectively. These earthquakes have a small magnitude and can only be detected at a
few stations.

only one P-pick or S-pick from each station is assigned to each earthquake. McBrearty, Gomberg, et al. (2019)
accounts for this constraint using a constrained ILP (integer linear programming) solution in their association method, and there is a strong correspondence between that technique and our technique. One potential
solution that would allow introduction of the station-based constraint is to add a normalizing scheme similar
to Equation 5 over stations. We adopt a simple post-processing filter to remove multiple picks from the same
ZHU ET AL.

12 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 13

10.1029/2021JB023249

Table 3
Comparison With Other Catalogs
SCSN
(10,151)

Ross et al. (2019)
(29,384)

Liu et al. (2020)
(15,421)

Shelly (2020)
(16,778)

Recall

0.94

0.61

0.95

0.89

Precision

0.42

0.81

0.69

0.65

F1-score

0.59

0.70

0.80

0.75

Catalog
GaMMA
(24,327)

station and keep only the pick with the minimum arrival time residual for each associated earthquake. Finally,
GaMMA assumes that the residuals of pick time or amplitude follow a Gaussian distribution. This assumption
is not accurate for false positive picks. For example, false-positive picks are not randomly distributed and
more likely to emerge from the coda of an event, other impulsive phases, or various noise sources. Adding a
mixture component of background uniform distribution to account for false positive picks might be a helpful
extension to be considered in future research (Melchior & Goulding, 2018). The amplitude measurement has
the potential to be biased by events that happen closely in time, earthquake radiation patterns, site amplification factors, and other issues that affect amplitudes. Accurately measuring amplitude information for events
occurring closely in time requires accurately detecting each event and then measuring the amplitude for the
proper phases of each event. New algorithms for improving amplitude measurement could further improve the
association performance of GaMMA.

5. Conclusions
We have developed a new phase association method, Bayesian Gaussian Mixture Model Association (GaMMA),
which solves the phase association problem as an unsupervised clustering problem. To consider the physical
constraints of phase arrival time and amplitude with earthquake location and magnitude, we incorporate optimization of earthquake location and magnitude into the EM algorithm that is commonly used for solving the
GMM. GaMMA can use both arrival time and amplitude information to cluster picks from the same earthquake
and simultaneously estimates both the earthquake location and magnitude from each cluster of picks. The experiment results for both synthetic tests and the 2019 Ridgecrest earthquake sequence demonstrate the effectiveness
of GaMMA in associating a dense sequence of P- and S-phase picks under realistic conditions. The improved
performance of GaMMA in association speed while using both time and amplitude information can associate
more earthquakes from massive automatic phase pick datasets, thus enriching earthquake catalogs and improving
earthquake monitoring.

Data Availability Statement
The phase picking and association data are available in Open Science Framework (https://doi.org/10.17605/OSF.
IO/3GP72). The code is open source in GitHub (https://doi.org/10.5281/zenodo.6271310). Gaussian Mixture
Model Association is developed based on the scikit-learn package (https://github.com/scikit-learn/scikit-learn).
The data of 2019 Ridgecrest earthquake can be accessed from Southern California Earthquake Data Center.

Acknowledgments
This work is supported by the Department of Energy Basic Energy Sciences
(DE-SC0020445).

ZHU ET AL.

References
Abramowitz, M., & Stegun, I. A. (1964). Handbook of Mathematical Functions with Formulas, Graphs, and Mathematical Tables (Vol. 55). US
Government printing office.
Al-Ismail, F., Ellsworth, W. L., & Beroza, G. C. (2020). Empirical and synthetic approaches to the calibration of the local magnitude scale, ML,
in southern Kansas. Bulletin of the Seismological Society of America, 110(2), 689–697. https://doi.org/10.1785/0120190189
Allen, R. V. (1978). Automatic earthquake recognition and timing from single traces. Bulletin of the Seismological Society of America, 68(5),
1521–1532. https://doi.org/10.1785/bssa0680051521
Arora, N. S., Russell, S., & Sudderth, E. (2013). NET-VISA: Network processing vertically integrated seismic analysis. Bulletin of the Seismological Society of America, 103(2A), 709–729. https://doi.org/10.1785/0120120107
Barrett, S., & Beroza, G. (2014). An empirical approach to subspace detection. Seismological Research Letters, 85, 594–600. https://doi.
org/10.1785/0220130152

13 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 14

10.1029/2021JB023249

Beroza, G. C., Segou, M., & Mostafa Mousavi, S. (2021). Machine learning and earthquake forecasting—Next steps. Nature Communications,
12(1), 1–3. https://doi.org/10.1038/s41467-021-24952-6
Bishop, C. M. (2006). Pattern recognition and machine learning. Springer.
Dickey, J., Borghetti, B., Junek, W., & Martin, R. (2020). Beyond correlation: A path-invariant measure for seismogram similarity. Seismological
Research Letters, 91(1), 356–369. https://doi.org/10.1785/0220190090
Draelos, T. J., Ballard, S., Young, C. J., & Brogan, R. (2015). A new method for producing automated seismic bulletins: Probabilistic event
detection, association, and location. Bulletin of the Seismological Society of America, 105(5), 2453–2467. https://doi.org/10.1785/0120150099
Ferguson, T. S. (1973). A Bayesian analysis of some nonparametric problems. Annals of Statistics, 209–230. https://doi.org/10.1214/
aos/1176342360
Fletcher, R. (2013). Practical methods of optimization. John Wiley & Sons.
Friberg, P., Lisowski, S., Dricker, I., & Hellman, S. (2010). Earthworm in the 21st century. In EGU general assembly conference abstracts
(p. 12654).
Gibbons, S. J., Kværna, T., Harris, D. B., & Dodge, D. A. (2016). Iterative strategies for aftershock classification in automatic seismic processing
pipelines. Seismological Research Letters, 87(4), 919–929. https://doi.org/10.1785/0220160047
Gibbons, S. J., & Ringdal, F. (2006). The detection of low magnitude seismic events using array-based waveform correlation. Geophysical Journal International, 165(1), 149–166. https://doi.org/10.1111/j.1365-246x.2006.02865.x
Gutenberg, B. (1956). The energy of earthquakes. Quarterly Journal of the Geological Society, 112(1–4), 1–6.
https://doi.org/10.1007/978-3-662-28668-5_1
Harris, D. B., & Dodge, D. A. (2011). An autonomous system for grouping events in a developing aftershock sequence. Bulletin of the Seismological Society of America, 101(2), 763–774. https://doi.org/10.1785/0120100103
Hauksson, E., Yang, W., & Shearer, P. M. (2012). Waveform relocated earthquake catalog for southern California (1981 to June 2011). Bulletin
of the Seismological Society of America, 102(5), 2239–2244. https://doi.org/10.1785/0120120010
Huber, P. J. (1992). Robust estimation of a location parameter. In Breakthroughs in statistics (pp. 492–518). Springer. https://doi.
org/10.1007/978-1-4612-4380-9_35
Klein, F. W. (2002). User’s guide to HYPOINVERSE-2000, a fortran program to solve for earthquake locations and magnitudes. US Geological
Survey. https://doi.org/10.3133/ofr02171
Liu, M., Zhang, M., Zhu, W., Ellsworth, W. L., & Li, H. (2020). Rapid characterization of the July 2019 Ridgecrest, California, earthquake
sequence from raw seismic data using machine-learning phase picker. Geophysical Research Letters, 47(4), e2019GL086189. https://doi.
org/10.1029/2019gl086189
McBrearty, I. W., Delorey, A. A., & Johnson, P. A. (2019). Pairwise association of seismic arrivals with convolutional neural networks. Seismological Research Letters, 90(2A), 503–509. https://doi.org/10.1785/0220180326
McBrearty, I. W., Gomberg, J., Delorey, A. A., & Johnson, P. A. (2019). Earthquake arrival association with backprojection and graph theory.
Bulletin of the Seismological Society of America, 109(6), 2510–2531. https://doi.org/10.1785/0120190081
Melchior, P., & Goulding, A. D. (2018). Filling the gaps: Gaussian mixture models from noisy, truncated or incomplete samples. Astronomy and
Computing, 25, 183–194. https://doi.org/10.1016/j.ascom.2018.09.013
Mousavi, S. M., Ellsworth, W. L., Zhu, W., Chuang, L. Y., & Beroza, G. C. (2020). Earthquake transformer—An attentive deep-learning model
for simultaneous earthquake detection and phase picking. Nature Communications, 11(1), 1–12. https://doi.org/10.1038/s41467-020-17591-w
Münchmeyer, J., Bindi, D., Sippl, C., Leser, U., & Tilmann, F. (2020). Low uncertainty multifeature magnitude estimation with 3-D corrections
and boosting tree regression: Application to North Chile. Geophysical Journal International, 220(1), 142–159. https://doi.org/10.1093/gji/
ggz416
Park, Y., Mousavi, S. M., Zhu, W., Ellsworth, W. L., & Beroza, G. C. (2020). Machine-learning-based analysis of the Guy-Greenbrier, Arkansas
earthquakes: A tale of two sequences. Geophysical Research Letters, 47(6), e2020GL087032. https://doi.org/10.1029/2020gl087032
Patton, J. M., Guy, M. R., Benz, H. M., Buland, R. P., Erickson, B. K., & Kragness, D. S. (2016). Hydra–the national earthquake information
center’s 24/7 seismic monitoring, analysis, catalog production, quality analysis, and special studies tool suite. US Department of the Interior,
US Geological Survey.
Peng, Z., & Zhao, P. (2009). Migration of early aftershocks following the 2004 Parkfield earthquake. Nature Geoscience, 2(12), 877–881. https://
doi.org/10.1038/ngeo697
Permuter, H., Francos, J., & Jermyn, I. (2006). A study of Gaussian mixture models of color and texture features for image classification and
segmentation. Pattern Recognition, 39(4), 695–706. https://doi.org/10.1016/j.patcog.2005.10.028
Picozzi, M., Bindi, D., Spallarossa, D., Di Giacomo, D., & Zollo, A. (2018). A rapid response magnitude scale for timely assessment of the high
frequency seismic radiation. Scientific Reports, 8(1), 8562. https://doi.org/10.1038/s41598-018-26938-9
Powers, D. M. (2020). Evaluation: From precision, recall and F-measure to ROC, informedness, markedness and correlation. arXiv preprint
arXiv:2010.16061.
Reynolds, D. A., & Rose, R. C. (1995). Robust text-independent speaker identification using Gaussian mixture speaker models. IEEE Transactions on Speech and Audio Processing, 3(1), 72–83. https://doi.org/10.1109/89.365379
Richter, C. F. (1935). An instrumental earthquake magnitude scale. Bulletin of the Seismological Society of America, 25(1), 1–32. https://doi.
org/10.1785/bssa0250010001
Ross, Z. E., Idini, B., Jia, Z., Stephenson, O. L., Zhong, M., Wang, X., et al. (2019). Hierarchical interlocked orthogonal faulting in the 2019
Ridgecrest earthquake sequence. Science, 366(6463), 346–351. https://doi.org/10.1126/science.aaz0109
Ross, Z. E., Meier, M.-A., Hauksson, E., & Heaton, T. H. (2018). Generalized seismic phase detection with deep learning. Bulletin of the Seismological Society of America, 108(5A), 2894–2901. https://doi.org/10.1785/0120180080
Ross, Z. E., Trugman, D. T., Azizzadenesheli, K., & Anandkumar, A. (2020). Directivity modes of earthquake populations with unsupervised
learning. Journal of Geophysical Research: Solid Earth, 125(2), e2019JB018299. https://doi.org/10.1029/2019jb018299
Ross, Z. E., Trugman, D. T., Hauksson, E., & Shearer, P. M. (2019). Searching for hidden earthquakes in southern California. Science, 364(6442),
767–771. https://doi.org/10.1126/science.aaw6888
Ross, Z. E., Yue, Y., Meier, M.-A., Hauksson, E., & Heaton, T. H. (2019). PhaseLink: A deep learning approach to seismic phase association.
Journal of Geophysical Research: Solid Earth, 124(1), 856–869. https://doi.org/10.1029/2018jb016674
SCEDC. (2013). Southern California Earthquake Center. Caltech. [Dataset].
Schubert, E., Sander, J., Ester, M., Kriegel, H. P., & Xu, X. (2017). DBSCAN revisited, revisited: Why and how you should (still) use DBSCAN.
ACM Transactions on Database Systems, 42(3), 1–21. https://doi.org/10.1145/3068335
Seydoux, L., Balestriero, R., Poli, P., De Hoop, M., Campillo, M., & Baraniuk, R. (2020). Clustering earthquake signals and background noises in
continuous seismic data with unsupervised deep learning. Nature Communications, 11(1), 1–12. https://doi.org/10.1038/s41467-020-17841-x

ZHU ET AL.

14 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth

## PDF page 15

10.1029/2021JB023249

Shelly, D. R. (2020). A high-resolution seismic catalog for the initial 2019 Ridgecrest earthquake sequence: Foreshocks, aftershocks, and faulting
complexity. Seismological Research Letters, 91(4), 1971–1978. https://doi.org/10.1785/0220190309
Shelly, D. R., Beroza, G. C., & Ide, S. (2007). Non-volcanic tremor and low-frequency earthquake swarms. Nature, 446(7133), 305–307.
https://doi.org/10.1038/nature05666
Tan, Y. J., Waldhauser, F., Ellsworth, W. L., Zhang, M., Zhu, W., Michele, M., et al. (2021). Machine-learning-based high-resolution earthquake
catalog reveals how complex fault structures were activated during the 2016–2017 central Italy sequence. The Seismic Record, 1(1), 11–19.
https://doi.org/10.1785/0320210001
Waldhauser, F., & Schaff, D. P. (2008). Large-scale relocation of two decades of northern California seismicity using cross-correlation and
double-difference methods. Journal of Geophysical Research, 113(B8). https://doi.org/10.1029/2007jb005479
Weber, B., Becker, J., Hanka, W., Heinloo, A., Hoffmann, M., Kraft, T., et al. (2007). SeisComP3—Automatic and interactive real time data
processing. In Geophysical Research Abstracts (Vol. 9).
Wishart, J. (1928). The generalised product moment distribution in samples from a normal multivariate population. Biometrika, 32–52. https://
doi.org/10.1093/biomet/20a.1-2.32
Woollam, J., Rietbrock, A., Leitloff, J., & Hinz, S. (2020). HEX: Hyperbolic event eXtractor, a seismic phase Associator for highly active seismic
regions. Seismological Research Letters, 91(5), 2769–2778. https://doi.org/10.1785/0220200037
Yeck, W. L., Patton, J. M., Johnson, C. E., Kragness, D., Benz, H. M., Earle, P. S., et al. (2019). GLASS3: A standalone multiscale seismic detection associator. Bulletin of the Seismological Society of America, 109(4), 1469–1478. https://doi.org/10.1785/0120180308
Yoon, C. E., O’Reilly, O., Bergen, K. J., & Beroza, G. C. (2015). Earthquake detection through computationally efficient similarity search.
Science Advances, 1(11), e1501057. https://doi.org/10.1126/sciadv.1501057
Zhang, M., Ellsworth, W. L., & Beroza, G. C. (2019). Rapid earthquake association and location. Seismological Research Letters, 90(6), 2276–
2284. https://doi.org/10.1785/0220190052
Zhu, L., Chuang, L., McClellan, J. H., Liu, E., & Peng, Z. (2021). A multi-channel approach for automatic microseismic event association using
RANSAC-based arrival time event clustering (RATEC). Earthquake Research Advances, 100008. https://doi.org/10.1016/j.eqrea.2021.100008
Zhu, W., & Beroza, G. C. (2018). PhaseNet: A deep-neural-network-based seismic arrival-time picking method. Geophysical Journal International, 216(1), 261–273. https://doi.org/10.1093/gji/ggy423

ZHU ET AL.

15 of 15

21699356, 2022, 5, Downloaded from https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB023249, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

Journal of Geophysical Research: Solid Earth
