# SKHASH: A Python Package for Computing Earthquake Focal Mechanisms

Source: skousmal-2024-skhash.pdf
Extraction: text-layer extraction; physical PDF page numbers, starting at 1.
Text-layer extraction does not reproduce figures and may imperfectly render formulas or tables.

## PDF page 1
SKHASH: A Python Package for
Computing Earthquake Focal
Mechanisms
Robert J. Skoumal*1 , Jeanne L. Hardebeck1 , and Peter M. Shearer2
Abstract
Cite this article as Skoumal, R. J.,
J. L. Hardebeck, and P. M. Shearer (2024).
SKHASH: A Python Package for
Computing Earthquake Focal
Mechanisms, Seismol. Res. Lett. 95,
2519–2526, doi: 10.1785/0220230329.
We introduce a Python package for computing focal mechanism solutions. This algorithm,
which we refer to as SKHASH, is largely based on the HASH algorithm originally written
in Fortran over 20 yr ago. HASH innovated the use of suites of solutions, spanning the
expected errors in polarities and takeoff angles, to estimate focal mechanism uncertainty.
SKHASH benefits from new features with flexible input formats and allows users to take
advantage of recent advances in constraining focal mechanisms for small magnitude or
poorly recorded earthquakes. The 3D locations of earthquakes and the velocity models
used are varied when finding acceptable solutions. As a result, source–receiver azimuths
are reflective of errors from the earthquake locations and velocity models, in addition to
the takeoff angles. Users can consider weighted P-wave first-motion polarities derived
from traditional or machine-learning picks, cross-correlation consensus, and/or imputa-
tion techniques using SKHASH. Focal mechanism solutions can also be further constrained
using traditional, machine learning, and/or cross-correlation consensus S/P amplitude
ratios. With improved reporting of individual and collective P polarity and S/P amplitude
misfits, users can better evaluate the success of the solutions and the quality of the mea-
surements. The reporting also makes it easier to identify potential issues with metadata,
including incorrectly reported station polarity reversals. In addition, by leveraging
vectorized operations, taking advantage of an efficient backend Python C Application
Programming Interface, and the use of a parallel environment, the Python SKHASH
routine may compute mechanisms quicker than the HASH routine.
Introduction
Earthquake focal mechanisms can provide information about
fault structures, rupture kinematics, and stress orientations.
We commonly determine an earthquake’s focal mechanism
by analyzing energy recorded across a seismic network as the
radiation pattern of P and S waves from an earthquake depend
on the orientation of the fault and how it slipped (i.e., strike-
slip, normal, reverse, or oblique). Assuming a double-couple
model, we can imagine a four-quadrant sphere encompassing
the point source. Two of these quadrants will have initial com-
pressional movement away from the source, and the other two
quadrants will have dilatational movement toward the source.
By determining the P-wave first motions recorded on seis-
mometers and the paths the energy traveled to each instru-
ment, we can identify the quadrant orientations that fit our
observations. We can also constrain the potential quadrant ori-
entations by considering the relative amplitudes of the P and S
waves recorded on the seismometers. The amplitudes of P
waves are largest near the compressional and tensional axes
while S waves are largest near the nodal planes. By looking
for quadrant orientations that match this amplitude pattern
in addition to the previously described P-wave first-motion
polarities, we can be more confident in how the quadrants
are oriented. The resulting solution that describes the quadrant
orientation is referred to as a focal mechanism.
When an earthquake is well recorded and an accurate veloc-
ity model can be determined, we can extract more information
about how the fault slipped and better interpret non-double-
couple sources. Moment tensor inversions can be performed
for larger (commonly M > 3.5–4.0) earthquakes recorded by
regional seismic networks by comparing Green’s functions
with observed data (e.g., Guilhem and Dreger, 2011). Similar
approaches can also be used to constrain the nodal planes for
smaller magnitude seismicity if the events are recorded on a
1. U.S. Geological Survey, Moffett Field, California, U.S.A.,
https://orcid.org/0000-
0002-5627-6239 (RJS);
https://orcid.org/0000-0002-6737-7780 (JLH); 2. University
of California, San Diego, La Jolla, California, U.S.A.,
https://orcid.org/0000-0002-
2992-7630 (PMS)
*Corresponding author: rskoumal@usgs.gov
© Seismological Society of America
Volume 95
•
Number 4
•
July 2024
•
www.srl-online.org
Seismological Research Letters
2519
Electronic Seismologist
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 2
local seismic network (e.g., Li et al., 2011). However, for the
ubiquitous M <∼4.0 earthquakes that do not occur near a
local network, dependable moment tensors often cannot be
produced. For these smaller magnitude (or otherwise poorly
recorded) earthquakes, we may instead assume a double-
couple source and compute focal mechanism solutions.
Although we have been largely limited to using individually
determined P-wave first-motion polarities and S/P amplitude
ratios to compute focal mechanisms in the past, recent
advancements have improved our ability to determine these
features. These advancements include making cross-correla-
tion relative polarity measurements (e.g., Shelly et al., 2016),
using machine learning to detect additional phases (e.g.,
Uchide, 2020; Cheng et al., 2023) or impute estimates for low
confidence or missing measurements (e.g., Skoumal, Shelly,
and Hardebeck, 2023), using Bayesian source inversion consid-
ering measurement uncertainties (e.g., Pugh et al., 2016), mak-
ing S/P ratio measurements on single-component instruments
(Shelly et al., 2022), and making cross-correlation relative S/P
ratio measurements (Skoumal, Hardebeck, and Shelly, 2023).
These techniques have allowed focal mechanisms to be
determined for even smaller magnitude or poorly recorded
earthquakes, allowing for greater insight into complex fault
geometries and behaviors (e.g., Shelly et al., 2023).
The FPFIT (Reasenberg and Oppenheimer, 1985) and
HASH (Hardebeck and Shearer, 2002, 2003) software packages
are commonly used to determine focal mechanisms. Both
algorithms use a grid search considering the possible strike,
dip, and rake solutions to identify the focal mechanism that
best describes the polarities. The HASH algorithm has addi-
tional features, including the abilities to consider uncertainties
in takeoff angles by varying the hypocentral depths and
velocity models that are considered. The FPFIT and HASH
algorithms were written in Fortran and are computationally
efficient, but they are do not include recent advancements
in focal mechanism determination. HASHpy (Williams, 2014)
allows users to call HASH subroutines using a Python wrapper,
but the previously mentioned limitations of the algorithm
still apply.
Here, we introduce the SKHASH algorithm (Skoumal et al.,
2024; see Data and Resources) written in Python. The primary
objectives of this algorithm are to make the computation of
focal mechanisms as easy and quick as possible for scientists
while also allowing users to take advantage of recent advance-
ments in generating focal mechanism solutions. Only two
freely available, widely used external Python packages are
required for SKHASH: NumPy (Harris et al., 2020) and pandas
(McKinney, 2010). These are among the most popular Python
packages (PyPI Stats, 2024) and are included by default in the
popular Anaconda Python distribution (Anaconda Software
Distribution, 2016). SKHASH can run on Linux, macOS, and
Windows using all currently supported versions of Python (as
of February 2024: v.3.8–3.12).
Method
The SKHASH algorithm (Fig. 1) is largely based on HASH
(Hardebeck and Shearer, 2002; 2003). Both algorithms use a
grid-search approach that identifies the set of acceptable focal
mechanism solutions given the inputted P polarity and S/P ratio
measurements. The grid search can be repeated considering dif-
fering combinations of variable inputs (e.g., hypocentral depths)
to produce suites of solutions. The variability of this resulting set
of acceptable models defines the uncertainty of the preferred
focal mechanism solutions. A primary objective of SKHASH is
to make computing focal mechanisms easier for a variety of
workflows. SKHASH has additional capabilities and features
that improve the ease of use, some of which we will describe
here. These include facilitating a variety of input formats, more
friendly error messaging, and automatic quality control report-
ing. The SKHASH algorithm was also created with recent
advancements (e.g., consensus polarities) and machine-learning
workflows in mind, allowing the results from these new tech-
niques to be easily incorporated into the inversion.
New features
Three principal inputs are necessary to compute a focal mecha-
nism: (1) takeoff angles; (2) source–receiver azimuths; and (3)
the corresponding observations (i.e., P-wave polarity and/or
S/P ratio measurements). As stated previously, given vertical
depth uncertainties and velocity models provided by the user,
HASH varies the hypocentral depths of earthquakes and
velocity models considered to compute suites of takeoff angles.
For source–receiver azimuths, HASH computes the azimuth
between the station and preferred epicentral location and does
not consider horizontal location uncertainties (Fig. 2a). With
SKHASH, the hypocentral location is varied in three dimen-
sions, which allows for variable takeoff angles and source–
receiver azimuths to be considered (Fig. 2b). If the azimuthal
and/or the takeoff uncertainty for a measurement exceeds a
value set by the user, the measurement can be automatically
discarded. The degree of benefit of considering horizontal
errors will depend on the source–receiver distances and hori-
zontal uncertainties. Large source–receiver distances and/or
negligible horizontal hypocentral uncertainties will yield small
variations in source–receiver azimuths, whereas instruments
close to the receiver and/or large uncertainties (Fig. 2b) will
result in larger azimuthal variations.
We add the functionality for custom weights to be used for
polarity measurements. This gives users much greater control
over the significance that individual polarity measurements have
on determining the resulting solution. The significance of a meas-
urement is denoted by the absolute value of the polarity value
ranging between −1.0 and 1.0 while the sign denotes the upward
(compressive) or downward (dilatational) movement.
The user has the option to automatically report misfits for
polarities and S/P ratios (Fig. 3). These can be reported for
individual measurements or as a collective for each receiver.
2520
Seismological Research Letters
www.srl-online.org
•
Volume 95
•
Number 4
•
July 2024
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 3
This reporting also makes it easier to identify potential issues
with the data and/or metadata, including incorrectly reported
station polarity reversals.
Usually, the polarity measurements recorded for a given
earthquake are used to compute a focal mechanism solution
for the event. Alternatively, measurements from multiple, sim-
ilar earthquakes can be used together to produce composite
mechanisms (e.g., Shelly et al., 2016). With the composite
mechanism approach, many earthquakes can contribute to a
single solution that represents the “family” of earthquakes.
This can help address the limitation of poor focal sphere cover-
age that is common for poorly recorded events. SKHASH is
capable of computing both single-event and composite focal
mechanism solutions (Fig. 4).
Recent advancements using cross correlation and machine
learning have improved the ability to constrain focal mechanisms,
and SKHASH is designed to
accommodate results from these
new techniques. Users have the
option of using any combination
of (1) traditional P-wave first
motions, (2) polarities identified
with deep learning (e.g., Uchide,
2020), (3) correlation consensus
polarities,
which
use
cross
correlation of phase arrivals to
identify (anti)similar waveforms
(e.g., Shelly et al., 2016), and (4)
imputed polarities, which fill in
missing or low-confidence mea-
surements using machine-learn-
ing techniques (e.g., Skoumal,
Shelly, and Hardebeck, 2023).
In addition, any combination
of traditional and relative S/P
ratio
measurements
derived
from single-component (Shelly
et
al.,
2022)
and
multi-
component stations (Skoumal,
Hardebeck, and Shelly, 2023)
can also be used. The measure-
ment sources are tracked, and
the accuracy of each measure-
ment type can be reported to
help users gauge the contribu-
tion from the different measure-
ment sources. These reports can
be automatically produced for
individual measurements as well
as collectively reported for each
receiver.
SKHASH offers better con-
trol
over
the
relationship
between station metadata and the polarity and S/P ratio mea-
surements. For example, when using HASH, polarity reversals
are applied to all instruments that share the station code within
a specified time window. With SKHASH, instrument locations,
reversals, and station correction measurements can be related
using any combination of the network, station, location, and
channel code metadata at multiple time windows. Although
we recommend using all network, station, location, and chan-
nel codes to associate measurements with the metadata when-
ever possible, being able to omit some metadata can still be
useful. For example, old HYPOINVERSE (Klein, 1989) phase
files do not include location codes.
Ease of use
With HASH, different versions of the Fortran code (“drivers”)
are compiled by the user depending on the format of input data
Figure 1. Algorithm flowchart of the modified HASH method (Hardebeck and Shearer, 2002, 2003)
used in SKHASH (Skoumal et al., 2024). Italicized, gray text designates optional (but recom-
mend) inputs and steps. The color version of this figure is available only in the electronic edition.
Volume 95
•
Number 4
•
July 2024
•
www.srl-online.org
Seismological Research Letters
2521
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 4
and type of analysis performed (e.g., whether S/P ratios are
included). Summarized briefly, the five drivers included in
HASH v.1.2 handle (1) P-wave polarities and precomputed
takeoff angles/azimuths, (2) P-wave polarities and 1D velocity
model(s) to compute the takeoff angles/azimuths, (3) P-wave
polarities and S/P ratios and velocity model(s) to compute the
takeoff angles/azimuths, (4) similar to (2) but with an updated
Southern California Earthquake Data Center phase format,
and (5) similar to (1) but using the takeoff angles/azimuths
from 3D ray tracing reported in the output file from
SIMULPS 3D (Evans et al., 1994). Users may create custom
Figure 3. Demonstration of the misfit reporting using the SKHASH
(Skoumal et al., 2024) example “smile” composed of synthetic
(a) P-wave polarities and (b) S/P ratios. The color version of this
figure is available only in the electronic edition.
Figure 2. Demonstration of source–receiver azimuthal calcula-
tions using (a) HASH (Hardebeck and Shearer, 2002, 2003) and
(b) SKHASH (Skoumal et al., 2024). With HASH, the takeoff
angles are varied but a single source–receiver azimuth is com-
puted between each epicenter (star) and receiver (triangle). With
SKHASH, in addition to varying the takeoff angles, the epicentral
location for each event can be varied given a horizontal error
(ERH) that results in a more representative reflection of the
potential source–receiver azimuths. The user has the option to
automatically discard measurements that exceed a given source–
receiver azimuthal uncertainty (θ). The color version of this figure
is available only in the electronic edition.
2522
Seismological Research Letters
www.srl-online.org
•
Volume 95
•
Number 4
•
July 2024
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 5
HASH drivers by modifying the existing code, but it requires
some level of Fortran proficiency and familiarity with the
algorithm.
With SKHASH, formatting of the user input files is more
flexible and handles varying inputs without the need of compil-
ing different versions of the code. SKHASH is fully compatible
with the file formats used for all five drivers included in
HASH v.1.2 (Fig. 5). In addition, SKHASH can also read the
new polarity formats produced by the Northern California
Earthquake Data Center (Northern California Earthquake
Data Center [NCEDC], 2014) as well as a new “free form” for-
mat (i.e., the ‘SKHASH’ format). When using this free form
format, users can provide a comma separated file with labeled
columns in any order and can handle virtually any amount of
whitespace or additional information.
User-defined variables are provided using a “control file,” a
human-readable text file. Variable names precede the desired
value, and these variables can be declared in any order. If a
value is not provided in the control file, the default value is
used. We have also attempted to make it as simple as possible
to run the code in parallel and to take advantage of an API that
calls a Fortran grid-search backend (both described later).
These features are completely optional, and whether each
feature used is controlled by a corresponding variable in the
control file.
Efficiency
Python is largely an interpreted scripting language where con-
verted byte code is executed in a virtual environment during
execution. By comparison, Fortran is a language that requires
code to be precompiled into a binary executable. As a result,
faster runtimes for a variety of applications can be expected
using Fortran than “pure” Python. To make the computation
of mechanisms more efficient using Python in SKHASH, many
operations are vectorized and the NumPy library is used, which
utilizes precompiled C code. Most of the computation time is
spent doing the grid search to find acceptable fault plane sol-
utions. With SKHASH, the user has the option to use a Python
C API that calls a Fortran grid-search subroutine. Provided
a Fortran compiler is available on the user’s machine, this
API is built automatically the first time the user requests
the use of the Fortran backend. In addition, calculating focal
mechanisms is an embarrassingly parallel problem and run-
times can be greatly improved using parallel processing. If
the user wishes, SKHASH can take advantage of Python’s
multiprocessing module and run in parallel by simply specify-
ing either a set number or all available Central Processing
Units on their machine.
SKHASH runtimes to produce focal mechanisms depend
on the user’s computer, whether the SKHASH Fortran grid
search is used, and the complexity of focal mechanism prob-
lem. Depending on these factors, SKHASH may produce focal
mechanisms with runtimes roughly equivalent to (or poten-
tially quicker than) HASH (Fig. 6). For tasks that involve the
computation of very large numbers of mechanisms or where
near-real-time results are needed, HASH may still be the better
suited tool provided only traditional P-wave polarities and
S/P measurements are needed. For small to moderate tasks,
Figure 4. Demonstration of composite focal mechanism solutions
produced by SKHASH (Skoumal et al., 2024) for two example
families of earthquakes with (a) ~N49°E and (b) ~N11°W strikes
(Shelly et al., 2023; Skoumal, Shelly, and Hardebeck, 2023) that
were part of an earthquake swarm that occurred in 2020 along
the Maacama fault, California. The color version of this figure is
available only in the electronic edition.
Volume 95
•
Number 4
•
July 2024
•
www.srl-online.org
Seismological Research Letters
2523
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 6
SKHASH and HASH runtimes may be virtually identical from
a user’s perspective. The flexibility of the inputs accepted by the
SKHASH algorithm may simplify the process from formatting
the input data allowing focal mechanisms to be computed
easier and quicker.
Application
In our software package (see Data and Resources), we provide a
user manual and examples of how to use SKHASH (Skoumal
et al., 2024). The examples include (1) duplication of the five
drivers used by HASH that demonstrate backward compatibil-
ity (“hash1-5”; Fig. 5), (2) synthetic P-wave polarities and S/P
ratios that demonstrate the quality reporting produced by
Figure 5. Demonstrating the backward compatibility of our
algorithm. Comparison of SKHASH (black; Skoumal et al., 2024)
and HASH (magenta; Hardebeck and Shearer, 2003) focal
mechanism solutions results for 24 earthquakes from the 1994
Northridge, California, sequence that were used in the five driver
examples included in HASH v.1.2. As the input data and
parameters are the same, the resulting solutions are virtually
identical with subtle variations explained by the differing Monte
Carlo trials. Note that two mechanisms are not produced using
the inputs for HASH driver 5 as the azimuthal gap exceeds the
user-defined value. The color version of this figure is available
only in the electronic edition.
2524
Seismological Research Letters
www.srl-online.org
•
Volume 95
•
Number 4
•
July 2024
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 7
SKHASH (“smile”; Fig. 3), and (3) composite mechanisms pro-
duced for the Maacama fault using correlation consensus
(“maacama”; Fig. 4).
Conclusions
The number of open-source Python tools for seismological
research have grown over the past couple of decades. Python
packages, such as ObsPy (e.g., Beyreuther et al., 2010), have
offered seismologists the ability to conduct research and scientific
support using streamlined workflows. Users familiar with Python
may find the SKHASH code easier to understand, use, and
modify for focal mechanism determination when compared with
the preceding Fortran routines. Although SKHASH is not
intended to be a complete replacement for all cases, we hope
the opportunity to compute focal mechanisms in streamlined
environments will be appealing
to many users. The improve-
ments to the ease of use may
appeal to scientists with limited
scientific programming experi-
ence,
and
the
capability
of
exploiting
several
recent
advancements in focal mecha-
nism determination may also
attract researchers interested in
the latest techniques. We plan
to integrate future techniques
into this SKHASH framework
so that new methods are more
accessible to the broader com-
munity, and we welcome all
who are interested to join in
its future development.
Data and Resources
The SKHASH software (Skoumal
et
al.,
2024;
doi:
10.5066/
P9MI5BUQ) is publicly available.
Python
(https://www.python.org),
the
NumPy
package
(https://
numpy.org), and the pandas pack-
age (https://pandas.pydata.org) are
all freely available. The HASH pro-
gram
(https://www.usgs.gov/node/
279393) is also freely available. All
websites
were
last
accessed
in
February 2024.
Declaration of
Competing
Interests
The authors acknowledge that
there are no conflicts of inter-
est recorded.
Acknowledgments
Ole Kaven and Justin Rubinstein provided helpful peer reviews that
improved the article. The authors thank Tim Clements and Armaan
Bhargava-Shah for testing the SKHASH algorithm. Any use of trade,
firm, or product names is for descriptive purposes only and does not
imply endorsement by the U.S. Government.
References
Anaconda Software Distribution (2016). Computer software, Anaconda
Vers. 2-2.4.0, available at https://anaconda.com/ (last accessed March
2024).
Beyreuther, M., R. Barsch, L. Krischer, T. Megies, Y. Behr, and J.
Wassermann (2010). ObsPy: A Python toolbox for seismology,
Seismol. Res. Lett. 81, no. 3, 530–533, doi: 10.1785/gssrl.81.3.530.
Figure 6. Runtimes of HASH v.1.2 using the five example drivers (“HASH”) compared with SKHASH
(Skoumal et al., 2024) using pure Python (“SKHASH”), the Python C API calling a Fortran grid-
search subroutine (“SKHASH, Fortran”), and the Python C API run in parallel on 24 threads
(“SKHASH, Parallel”). Runtimes were computed using 2xIntel Xeon Gold 5217 Processors. Each
implementation was run 10 times, and the average system runtime to compute a mechanism are
shown. Standard deviations of the runtimes were all <0.01 s. The color version of this figure is
available only in the electronic edition.
Volume 95
•
Number 4
•
July 2024
•
www.srl-online.org
Seismological Research Letters
2525
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026

## PDF page 8
Cheng, Y., E. Hauksson, and Y. Ben-Zion (2023). Refined earthquake
focal mechanism catalog for southern California derived with deep
learning algorithms, J. Geophys. Res. 128, e2022JB025975, doi:
10.1029/2022JB025975.
Evans, J. R., D. Eberhart-Phillips, and C. H. Thurber (1994). User’s
manual for SIMULPS12 for imaging VP and VP/VS; a derivative
of the “Thurber” tomographic inversion SIMUL3 for local earth-
quakes and explosions (No. 94-431), US Geol. Surv. Open-File
Rept. OF 94-0431, 101 pp., doi: 10.3133/ofr94431.
Guilhem, A., and D. S. Dreger (2011). Rapid detection and characteri-
zation of large earthquakes using quasi-finite-source Green’s func-
tions in continuous moment tensor inversion, Geophys. Res. Lett.
38, no. 13, doi: 10.1029/2011GL047550.
Hardebeck, J. L., and P. M. Shearer (2002). A new method for deter-
mining first-motion focal mechanisms, Bull. Seismol. Soc. Am. 92,
no. 6, 2264–2276, doi: 10.1785/0120010200.
Hardebeck, J. L., and P. M. Shearer (2003). Using S/P amplitude ratios
to constrain the focal mechanisms of small earthquakes, Bull.
Seismol. Soc. Am. 93, no. 6, 2434–2444, doi: 10.1785/0120020236.
Harris, C. R., K. J. Millman, S. J. van der Walt, R. Gommers, P.
Virtanen, D. Cournapeau, E. Wieser, J. Taylor, S. Berg, and N.
J. Smith, et al. (2020). Array programming with NumPy,
Nature 585, 357–362, doi: 10.1038/s41586-020-2649-2.
Klein, F. W. (1989). User’s guide to HYPOINVERSE, a program for VAX
computers to solve for earthquake locations and magnitudes, Vol. 89,
US Department of the Interior, Geol. Surv. doi: 10.3133/ofr89314.
Li, J., H. Zhang, H. Kuleli Sadi, and M. Toksoz Nafi (2011). Focal
mechanism determination using high-frequency waveform match-
ing and its application to small magnitude induced earthquakes,
Geophys. J. Int. 184, no. 3, 1261–1274, doi: 10.1111/j.1365-
246X.2010.04903.x.
McKinney, W. (2010). Data structures for statistical computing in
python, Proc. of the 9th Python in Science Conference, Austin,
Texas, 28 June–3 July 2010, Vol. 445, 51–56.
Northern California Earthquake Data Center (NCEDC) (2014). UC
Berkeley seismological laboratory, dataset, doi: 10.7932/NCEDC.
Pugh, D. J., R. S. White, and P. A. F. Christie (2016). A Bayesian
method for microseismic source inversion, Geophys. J. Int. 206,
no. 2, 1009–1038, doi: 10.1093/gji/ggw186.
PyPI Stats (2024). Analytics for PyPI packages, available at https://
pypistats.org (last accessed March 2024).
Reasenberg, P. A., and D. H. Oppenheimer (1985). FPFIT, FPPLOT,
and FPPAGE: Fortran computer programs for calculating and dis-
playing earthquake fault-plane solutions, U.S. Geol. Surv. Open-
File Rept. 85-739, doi: 10.3133/ofr85739.
Shelly, D. R., J. L. Hardebeck, W. L. Ellsworth, and D. P. Hill (2016). A
new strategy for earthquake focal mechanisms using waveform-cor-
relation-derived relative polarities and cluster analysis: Application
to the 2014 Long Valley caldera earthquake swarm, J. Geophys. Res.
121, 8622–8641, doi: 10.1002/2016JB013437.
Shelly, D. R., R. J. Skoumal, and J. L. Hardebeck (2022). S/P Amplitude
ratios derived from single-component seismograms and their
potential use in constraining focal mechanisms for microearth-
quake sequences, Seism. Record 2, no. 2, 118–126, doi: 10.1785/
0320220002.
Shelly, D. R., R. J. Skoumal, and J. L. Hardebeck (2023). Fracture-mesh
faulting in the swarm-like 2020 Maacama sequence revealed by
high-precision earthquake detection, location, and focal mecha-
nisms, Geophys. Res. Lett. 50, no. 1, doi: 10.1029/2022GL101233.
Skoumal, R. J., J. L. Hardebeck, and P. M. Shearer (2024). SKHASH: A
Python package for earthquake focal mechanism inversions (version
1.0.0), U.S. Geol. Surv. Software Release, doi: 10.5066/P97FBHTL.
Skoumal, R. J., J. L. Hardebeck, and D. R. Shelly (2023). Using cor-
rected and imputed polarity measurements to improve focal mech-
anisms in a regional earthquake catalog near the Mt. Lewis fault
zone, California, J. Geophys. Res. 128, no. 2, e2022JB025660, doi:
10.1029/2022JB025660.
Skoumal, R. J., D. R. Shelly, and J. L. Hardebeck (2023). Using
machine learning techniques with incomplete polarity datasets
to improve earthquake focal mechanism determination, Seismol.
Soc. Am. 94, no. 1, 294–304, doi: 10.1785/0220220103.
Uchide, T. (2020). Focal mechanisms of small earthquakes beneath
the Japanese islands based on first-motion polarities picked using
deep learning, Geophys. J. Int. 223, no. 3, 1658–1671, doi: 10.1093/
gji/ggaa401.
Williams, M. C. (2014). HASHpy, doi: 10.5281/zenodo.9808.
Manuscript received 2 October 2023
Published online 10 April 2024
2526
Seismological Research Letters
www.srl-online.org
•
Volume 95
•
Number 4
•
July 2024
Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​95/​4/​2519/​6525037/​srl-2023329.​1.​pdf by China Univ of Geosciences Library  Wuhan user on 24 September 2026
