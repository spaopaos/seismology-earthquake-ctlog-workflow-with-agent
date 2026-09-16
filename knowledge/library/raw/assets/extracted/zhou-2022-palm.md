# An Earthquake Detection and Location Architecture for Continuous Seismograms: Phase Picking, Association, Location, and Matched Filter (PALM)

Source: zhou-2022-palm.pdf
Extraction: pdftotext; physical PDF page numbers, starting at 1.
Text-layer extraction does not reproduce figures and may imperfectly render formulas or tables.

## PDF page 1

Electronic Seismologist

An Earthquake Detection and
Location Architecture for
Continuous Seismograms: Phase
Picking, Association, Location, and
Matched Filter (PALM)
Yijian Zhou1 , Han Yue2,3, Lihua Fang4,5, Shiyong Zhou*2,3, Li Zhao2,3 , and
Abhijit Ghosh1

Abstract
We developed an earthquake detection and location architecture for continuous seismograms that incorporates phase picking, phase association, location, and matchedfilter techniques (PALM). The PALM architecture incorporates two modules: (1) PAL,
the initial detection following picking, association, and location processes, and
(2) match, expand, shift, and stack (MESS), a matched-filter detector that augments
the template catalog. The effectiveness of PALM is demonstrated in building an early
aftershock catalog for the 2019 Ridgecrest, California, earthquake. By comparing with
Southern California Seismic Network arrival times, we show that the PAL picker combines the strengths of short-term average/long-term average and the kurtosis picker,
realizing robust phase detection and precise picking. Our final MESS catalog is compared with two other matched-filter catalogs by Ross, Idini, et al. (2019) and Shelly
(2020). We find that PALM directly recovers unbiased and detailed features in seismicity
from continuous seismograms, which can be efficiently implemented to scan continuous waveforms without the need for visual inspection.

Introduction
The detection and location of seismic events are basic procedures for generating earthquake catalogs. A catalog with high
completeness and high resolution provides a detailed image of
3D fault geometry (Waldhauser and Ellsworth, 2002; Hayes
et al., 2012; Shelly et al., 2016; Ross et al., 2017), which
facilitates the fault model construction to perform slip model
inversions, (e.g., (Yue et al., 2017; Sun et al., 2018). The spatiotemporal pattern and magnitude scaling also provide
insights into the physical processes on fault, for example,
slow-slip migration (Peng and Zhao, 2009; Kato et al., 2016)
and fluid diffusion (Di Luccio et al., 2010; Chen et al., 2012);
The power-law distribution of events at different magnitudes is
described by the b-value, which is observed to be correlated
with stress level, fault roughness, and fault strength (Scholz,
1968; Schorlemmer and Wiemer, 2005; Spada et al., 2013).
In general, an ideal earthquake catalog should have high
completeness, location precision, and consistent performance
over a long time scale. Realizing this objective in modern
networks, which typically include hundreds to thousands of
stations, requires a high-performance detection and location
Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

Cite this article as Zhou, Y., H. Yue,
L. Fang, S. Zhou, L. Zhao, and A. Ghosh
(2021). An Earthquake Detection and
Location Architecture for Continuous
Seismograms: Phase Picking, Association,
Location, and Matched Filter (PALM),
Seismol. Res. Lett. 93, 413–425,
doi: 10.1785/0220210111.

Supplemental Material

architecture to perform automatic and systematic scanning
over continuous waveforms.
The detection of earthquakes is usually based on a network
of seismic stations. Typical detection workflows involve
(1) phase picking on single stations and (2) associating picks
into events. Before the application of artificial intelligence (AI)
seismology, automatic phase picking was usually realized with
energy-based characteristic functions, for example, short-termaverage over long-term-average (STA/LTA; Allen, 1978),
which captures the abrupt change of amplitude in the seismograms. This type of methods presents high computational efficiency, but it tends to introduce a high false detection rate and
1. Department of Earth Sciences, University of California, Riverside, California, U.S.A.,
https://orcid.org/0000-0002-7205-1769 (YZ);
https://orcid.org/0000-00020557-2839 (AG); 2. Institute of Theoretical and Applied Geophysics, Peking
https://orcid.org/0000-0002-0950-6863 (LZ); 3. Hebei
University, Beijing, China,
Hongshan Geophysical National Observation and Research Station, Peking University,
Beijing, China; 4. Institute of Geophysics, China Earthquake Administration, Beijing,
China; 5. Key Laboratory of Earthquake Source Physics, China Earthquake
Administration, Beijing, China
*Corresponding author: zsy@pku.edu.cn
© Seismological Society of America

Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

413

## PDF page 2

does not discriminate P and S wave well. To overcome this
limitation, proper association algorithms enable more accurate
detection, though station records with a low signal-to-noise
ratio (SNR) may still be missed. The phase association is usually realized by the temporal and spatial correlation between
picks (Johnson et al., 1997; Patton et al., 2016; White et al.,
2019), but differences exist in the format of input picks. For
example, Chen and Holland (2016) do not assign P or S to
the picks and let the associator decide each pick to be P/S;
Zhang et al. (2019) need P and S picks, but they do not come
in pairs, which leads to low efficiency.
In more recent years, two types of algorithms have presented better detection performance: AI and matched-filter
technique (MFT). AI-based phase pickers incorporate the features of complete waveform (i.e., P and S phases), instead of
solely the phase arrivals (Zhu and Beroza, 2018; Zhou et al.,
2019; Mousavi et al., 2020). With numerous labeled training
samples, AI models are able to detect and pick emergent phase
arrivals. However, training samples are not always available,
and pretrained models cannot guarantee performance comparable to that on the training set (Zhu et al., 2019; Chai et al.,
2020). Such attempts in this direction include transfer learning
(Zhu et al., 2019; Chai et al., 2020) and building a global
training set (Mousavi et al., 2019; Liu et al., 2020). Even so,
AI applicants still suffer from the difficulty in collecting and
preprocessing training data, as well as building efficient training pipelines for big data. Thus, though a promising and fastdeveloping direction, AI pickers need additional case studies to
validate their effectiveness and robustness.
Matched-filter augments the initial detections (i.e., templates)
by cross correlating with raw data (Turin, 1960; Gibbons and
Ringdal, 2006). This correlation-based algorithm can detect signals lower than the noise level and can thus obtain the most
complete catalog (Shelly et al., 2007). However, the detectability
of MFT is determined by the diversity of template waveforms,
which requires a rather complete catalog and high seismicity
rate. Moreover, the cross correlation is computationally expensive, even with adopting a graphics processing unit (GPU) acceleration. These shortcomings limit the applicability of MFT to
certain situations, for example, aftershock detection in which
enough templates are available and only a few days of scanning
is required. Thus, an ideal automatic detection workflow should
provide reliable baseline detections as templates and an efficient
MFT implementation based on GPU acceleration.
The location of earthquakes is usually based on arrival times
picked for each event. Typical location processes include
(1) absolute location, in which each event is located individually,
thus minimizing the difference between observed and predicted
travel times (Geiger, 1912; Klein, 2002), and (2) relative location,
in which differential travel times for event pairs are measured to
constrain the relative location (Waldhauser and Ellsworth, 2000;
Zhou et al., 2001; Trugman and Shearer, 2017). In such a workflow, the absolute location process obtains an accurate overall
414

Seismological Research Letters

location, and the relative relocation helps to resolve a detailed
image of seismicity. An accurate absolute location calls for
high-quality phase picking, proper choice of velocity model,
adequate coverage of network, and fine-tuned location parameters (Husen and Hardebeck, 2010; Lomax, 2020). The picking
of S arrival is especially important in this process because the S-P
time constrains the length of the ray path, which reduces the
trade-off between the origin time and epicentral depth in the
inversion. However, S arrival is more difficult to precisely pick
in comparison with P arrivals because its initial arrival is often
contaminated by the tail of the P wave. This results in large
uncertainty in determining the hypocentral depths. The relative
relocation process resolves fine structure with the double-difference algorithm. Differential travel times measured by cross-correlation (CC) reach a theoretical resolution below the sampling
rate (Frémont and Malone, 1987); thus, it has always been
applied in company with MFT applications in recent years
(Shelly et al., 2016; Ross, Trugman, et al., 2019), which results
in both high detectability and high-resolution relocation.
The aforementioned progress makes possible a high-performance earthquake detection and location applied to modern
networks. However, people still need to combine modules from
different research studies, which possibly brings about low-efficiency pipelines and even errors. We acknowledge some successful cases following such a strategy (e.g., Mendoza et al., 2019;
White et al., 2019), but a seamless and open-source architecture
sequentially performing event detection, location, and match filter from raw data is still an urgent need of the seismic community. In this study, we present PALM, a newly developed
detection and location architecture applied to raw continuous
waveforms that incorporates phase picking, phase association,
location, and matched filter. PALM is independent of any a priori information about earthquakes, which gives high-completeness detection and high-resolution location. We apply it to the
2019 M w 7.1 Ridgecrest, California, (RC) aftershock sequence
and compare our result with two other MFT catalogs: Ross,
Idini, et al. (2019) and Shelly (2020) to validate its performance.

Method and Data
Workflow of PALM
The workflow of PALM includes two modules (Fig. 1):
(1) PAL, that is, picking, association, and location, an STA/
LTA-based algorithm for initial detection, and (2) MESS, that
is, match, expand, shift, and stacking, a matched-filter detector
that augments the initial PAL catalog. Each module contains
detection and location stages and processes raw continuous
waveforms. Details of PAL and MESS are presented in the
following sections. Suggestions for software usage can be found
in the supplemental material, available to this article.
PAL
The initial catalog is obtained by the PAL process, which
includes three steps (Fig. 1): (1) picking: the picker first picks
www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 3

and linear trend, tapering, and
band-pass filtering to the frequency band of local earthquakes. In the case of RC,
we apply a 2–40 Hz band-pass
filter. Then, the picking operation is performed on the processed data.
The P arrivals are detected
on the Z-component with the
STA/LTA algorithm (Fig. 2a).
The characteristic function
Sp det is calculated on the kinematic energy of the vertical
component:
EQ-TARGET;temp:intralink-;df3;433;548

Sp

det t

 Sz2 t;

3

Figure 1. Workflow of phase picking, phase association, location, and matched-filter (PALM)
techniques. Input and output results are denoted by squares. Detection and location operations are
plotted in ellipse patches. Modules for detection and location purposes are plotted in blue and
orange, respectively. MFT, matched-filter technique; MESS, match, expand, shift, and stack; PAL,
picking, association, and location. The color version of this figure is available only in the electronic
edition.

P and S arrivals from the continuous waveform; (2) association:
the associator groups phases to different events for location
purposes; and (3) location: events are located and relocated
with standard algorithms, that is, HYPOINVERSE (Klein,
2002) and HypoDD (Waldhauser, 2001).
PAL picker. The PAL picker picks P and S arrivals in pairs,
following a “detect and pick” strategy (Fig. 2). It is realized with
a combination of STA/LTA (Allen, 1978) and the Kurtosis
(Baillard et al., 2013) algorithm, the definitions of which are

EQ-TARGET;temp:intralink-;df1;41;275

Pti ΔtSTA
dτ i 
Δt LTA
t
Sd t i  
× Ptii
;
Δt STA
dτ i 
t −Δt
i

1

in which z is the Z-channel
velocity. The Δt STA is relatively
long for detection purposes. For
RC data, we set Δt STA  0:8 s
and Δt LTA  6 s. A detection
is declared at the triggering time
t p trig if Sp det reaches the triggering threshold Sp thres , that
is, Sp det t p trig   Sp thres . We set Sp thres  12 in RC based
on the estimation of the SNR. Precise P arrivals (t P ) are picked
around the triggering time by an STA/LTA operation calculated
on the vertical energy, but with a shorter Δt STA (Fig. 2b). We set
Δt STA  0:4 s and Δt LTA  2 s for P-arrival picking in RC. The
initial picking is made at the peak of the STA/LTA function,
which is then corrected on the Z-velocity by finding the first
peak backward.
S-wave arrivals are detected on the horizontal components
(E and N channels) (Fig. 2c). The triggering time for S-wave
t s trig is defined as the time when the S-wave amplitude AS t
reaches its peak value:

LTA

EQ-TARGET;temp:intralink-;df4;308;249

in which Sd is the STA/LTA function for the input waveform
(time series) d Δt LTA and Δt STA are the window lengths for
STA and LTA calculation, respectively. And

EQ-TARGET;temp:intralink-;df2;41;184

Pt i
1
4
t −Δt dτ i  − d̄
N
h
i ;
K d t i   P i K
ti
1
2 2
dτ

−
d̄
i
t i −Δt K
N

Volume 93

•

Number 1

•

January 2022

EQ-TARGET;temp:intralink-;df5;308;171

•

www.srl-online.org

for t P < t i < t P  Δt S ;

4

in which Δt S is the searching window for S wave following
the picked P-arrival time t P . The S-wave amplitude AS is
defined as

2

in which K d is the kurtosis function of data (d); Δt K and N are
the window length and number of sample points for kurtosis
calculation, respectively; and d and d̄ are the input data (time
series) and mean value of dτ for t i − Δt K < τ i ≤ t i , respectively. The raw data are preprocessed by removing the mean

AS t strig   maxAS t i ;

( p
x2 t i y2 t i  ×Pfilter ; fort p <t i ≤t p Δt filter

AS t i  p
;
fort p Δt filter <t i <t p Δt S
x2 t i y2 t i ;
5

in which Pfilter is a polarization filter based on principal component analysis (see supplemental material) and Δt filter is the
time window in which the polarization filter is applied. We set
Δt filter  2 s in RC to remove the possible contamination from
Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

415

## PDF page 4

(a)

(c)

(b)

(d)

(e)

the P wave. The S arrival is thus constrained between
t P  t s trig − t P =2 and t s trig (namely “S window”).
Precise S-arrival time t S is picked by the kurtosis of the horizontal energy, with a small Δt K (i.e., K short ) to capture the
emergent change in amplitude (Fig. 2d,e). The correct peak
in K short is further constrained by STA/LTA, Ss det , and
long-window kurtosis K long in the S window (Fig. 2e):

EQ-TARGET;temp:intralink-;df6;53;392

Ss det t min   maxSs det 
K long t max  Δt corr   maxK long 

;

6

in which t min and t max are the earliest and latest boundaries of
the peak in K short and Δt corr is the time correction made by
finding the first trough backward. In RC, we set Δt STA  1 s
and Δt LTA  2 s to calculate Ss det and set Δt K  1 s and
Δt K  5 s to calculate K short and K long , respectively. The initial
picking is made at the peak of K short , which is then corrected on
the horizontal energy by finding the first peak backward.
The PAL picker provides precise P and S picks for correctly
detected phases. However, it may yield false detections due to
impulsive noise signal (Withers et al., 1998; Yue et al., 2018).
We conduct a subsequent phase association process to remove
false detections.
PAL associator. The P/S arrivals are associated with different
events based on their spatial and temporal relations at different
stations (Fig. 3). The temporal association is realized by
clustering the estimated origin times (Fig. 3a). The origin
time t o at a given station is estimated as

to 

EQ-TARGET;temp:intralink-;df7;53;106

416

tP × V P − tS × V S
;
VP − VS
Seismological Research Letters

7

Figure 2. Algorithm of PAL picker. (a) Detection of P arrival.
Z-channel waveform (velocity record) and short-term average/
long-term average (STA/LTA) function are plotted in black lines.
The trigger level and time are plotted by the dashed horizontal
gray line and yellow star, respectively. The P phase window is
bounded by gray-dashed rectangles. (b) Picking of P wave. Red
dashed and solid lines plot initial and corrected (final) P picks,
respectively. (c) Detection of S arrival. Original and principal
component analysis (PCA)-filtered horizontal (E-N) channel
amplitude are plotted in the top and bottom panels, respectively.
The time of maximum filtered amplitude is marked by the yellow
star. The S-phase window is marked as the gray-dashed rectangle
and gray double arrow. The red double arrow marks the first half
of the window between P and the yellow star (i.e., P window).
(d) Picking of S wave. The labels are identical as in panel (b).
(e) Detailed illustration of the S-picking algorithm. Characteristic
functions are plotted in black lines. The earliest and latest
boundaries derived from STA/LTA and the long-window kurtosis
picker are marked by gray-dashed lines. The initial and final S
picks are marked by red-dashed and solid lines, respectively. The
color version of this figure is available only in the electronic
edition.

in which V P and V S are the average P- and S-wave velocities in
the crust, respectively. In the case of RC, phase picks are
grouped into the same events if their origin-time estimations
deviate within 2 s. Temporally associated phase picks are
retained for further processing in the spatial association.
Epicentral distances can be roughly estimated from t S − t P ,
drawing a location circle centered by the station (Fig. 3b). For
point source (earthquake), these circles from different stations
converge near the real epicenter. This convergence serves as a
criterion for spatial association, which can eliminate arrivals
inconsistent with the common convergence point (i.e., false
www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 5

(a)

(b)

detection). This spatial association is realized by a 3D grid
search for the epicentral location that minimizes the traveltime residual ε defined as

EQ-TARGET;temp:intralink-;df8;41;392

ε

N
X

εi 

i1

N
X

jt o  T P;i  − t P;i j;

for εi < εmax ;

8

i1

in which T P;i and εi are the respective P-wave theoretical travel
time and residual at the ith station, respectively, and N is the
number of stations with travel-time residuals that fall below the
threshold εmax . We set εmax  1:5 s for the RC events, considering the uncertainty in travel-time estimation. A minimum
number of stations is required for a robust location, which
is set as N ≥ 4 here.
Finally, we estimate the local magnitude M L using the
S-wave amplitude, according to the classical definition by
Richter (1935):
EQ-TARGET;temp:intralink-;df9;41;197

M L  medianlog10 AS;i   log10 r i   1;

9

in which AS;i is the S-wave amplitude (in μm) at the ith station
and ri is the corresponding hypocentral distance in kilometers.
We do not include distance attenuation or the station correction term for wider applicability because they are path and site
dependent and are not available in most cases (Boore, 1989).
This results in a similar magnitude scale in California and
thus is suitable for the case of RC (Hutton and Boore, 1987;
Uhrhammer et al., 2011).
Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

Figure 3. Phase association process. (a) Temporal association.
E-channel waveforms at different stations are plotted in different
colors. Vertical solid-gray lines mark the picked P- and S-arrival
times. Yellow stars denote the estimated origin times. (b) Spatial
association. Red triangles show the locations of seismic stations.
Circles are centered at the stations with corresponding epicentral
distances estimated from the picked P- and S-arrival times. Yellow
stars denote the estimated epicenter. The color version of this
figure is available only in the electronic edition.

The PAL associator utilizes pairs of P-S picks to realize stable and efficient associations, which is different from previous
algorithms (e.g., Chen and Holland, 2016). This may result in
more missed detections when the network is rather sparse or
the noise level is high. This problem can be solved with the
following MESS detection procedure.
PAL locator. We adopt standard location and relocation procedures in the location stage because the PAL detector and
associator produce absolute arrival times. The detected events
are first located using HYPOINVERSE (Klein, 2002), which is
an absolute location method based on gradient descent inversion. Then, the locations are refined by HypoDD (Waldhauser,
2001), using the catalog-derived differential time (namely dt.ct)
(Fig. 1). The original PAL catalog serves as template events for
MESS detection, and the relocated PAL location is applied in
relocating MESS detection results.
Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

417

## PDF page 6

Template and raw waveforms

Epicentral distances (km)

(a)

Cross-correlation traces

(b)

Expand, shift and stack

Raw waveform
Template waveform

Travel time (s)

Travel time (s)

For RC events, we employ the 1D velocity model used by
Shelly (2020), which is a 1D approximation of the 3D
Community Velocity Model for Southern California model
(Kohler et al., 2003) (Fig. S9). In the absolute location using
HYPOINVERSE, we apply a cosine distance weighting factor
that changes from 1 at 30 km to 0 at 90 km and a residual
weighting function that ranges from 1 at 0.3 s to 0 at 0.9 s
of maximum residual for P and S picks. In the HypoDD
relocation, we set the parameter WDCT to 5 km and apply
four iterations of inversion, considering the average interevent
distance.

Relative arrival time (s)

Figure 4. Algorithm of MESS. (a) Matched filter. Template and raw
waveforms are plotted in red and gray lines, respectively. The
resulting cross correlations are plotted in black. (b) Stacking
strategy. Original and expanded cross correlations are plotted in
gray and black lines, respectively. The color version of this figure
is available only in the electronic edition.

2. Expand: a peak value expanding operation is imposed on
the cross-correlation functions (Fig. 4b):

CCpeak ; fort peak −Δt exp =2<t i ≤t peak Δt exp =2
CCexp t i 
;
CC0 t i ; otherwise
EQ-TARGET;temp:intralink-;df11;320;366

MESS
MESS detection. The initial PAL detections are augmented
by MESS, a matched-filter detector that consists of four steps:
match, expand, shift, and stack. In this process, both event detection and phase picks are realized by cross correlation, which is
accelerated by the GPU. The details of MESS are described as
follows:
1. Match: the similarity between template and raw data is
quantified by the cross correlation (Fig. 4a):

EQ-TARGET;temp:intralink-;df10;53;210

Pti Δttemp
d raw τ i  × d temp τ i − t i 
τ i t i
q ;
CC0 t i   q
PΔt temp 2
Pt i Δt temp 2
d
τ
×
raw i
τ i t i
τ i 0 d temp τ i 
10

in which d raw and dtemp are the raw and template waveforms,
respectively, and Δt temp is the length of the template waveform. For the RC data, the template uses 10 s windows, from
1 s before to 9 s after the P arrival, to cover both P and S waves
for accurate detection. Both template and raw waveforms are
preprocessed in the same way as in the PAL process.
418

Seismological Research Letters

11
in which CCpeak and t peak are the amplitude and time of the
CC0 peaks, respectively, and Δt exp is the length of expansion.
The expansion operation is designed to reconcile location
differences between the templates and detected events
because a direct summation fails to align peak CC values
at the origin time of the detected event, which limits the
detectability (see the comparison in Fig. 4b). We set
Δt exp  1 s in RC, which corresponds to a searching radius
of about 3 km around the template event.
3. Shift: The expanded cross correlation is shifted by the
P-wave travel time of the template event (Fig. 4b):
EQ-TARGET;temp:intralink-;df12;320;170

CCt i   CCexp t i  T P ;

12

in which T P is the P-wave travel time of the template event.
Given that the template event has a similar location to the
detected event, this time shift can roughly align the cross
correlations from different stations.
4. Stack: The migrated CCs from different stations are stacked
(Fig. 4b):
www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 7

EQ-TARGET;temp:intralink-;df13;41;743

CCstack t i  

N
1 X
×
CCi t i ;
N i1

13

in which N is the number of stations. Multitrace stacking
suppresses uncorrelated random noises, further reducing
the false detection rate. We set the detection criterion as
CCstack ≥ 0:25, and the origin time t o is determined as
the peak time on CCstack .
The P- and S-arrival times are then picked by waveform cross
correlation. The template window for CC picking ranges from
0.5 s-pre to 1.5 s-post the P arrival and from 0.5 s-pre to 2.5 spost the S arrival, considering the length of the signal in RC. The
S amplitude is also individually measured for magnitude estimation using the same method as that for PAL detections.
MESS relocation. The MESS detections are relocated by
HypoDD (Waldhauser, 2001), using the correlation measured
differential time as the dt.cc file (Fig. 1). Detections from
different templates are first associated based on their origin
time. In RC, we associate detections with estimated t o within
2 s as one detection, and its origin time is the t o estimation by
the template with the maximum CCstack value. The differential
travel time between the template and detected event is
obtained by
EQ-TARGET;temp:intralink-;df14;41;418

ΔT  t cc − t o − T temp ;

14

in which t cc is the correlation picked arrival time, t o is the origin time of the detected event, and T temp is the travel time of
the template event. The initial location of the templates is
shifted to the relocated PAL catalog location, whereas the initial location of newly detected events is set to the average of
template locations that detected it.
For RC events, we adopt the same velocity model as for the
PAL location. For robust relocation, each event is required to
be detected by at least three templates with dt from four
stations. We utilize only dt.cc to relocate MESS detections,
with the parameter WDCC set to 4 km for five iterations of
relocation.

Southern California Seismic Network (SCSN) data
We use the aftershock catalog of the 2019 Ridgecrest earthquake to validate the performance of the PALM pipeline.
The detected arrival time and relocated catalog are compared
with published results. We utilize publicly available SCSN data
to build the RC aftershock catalog (Cochran et al., 2020;
Hauksson et al., 2020). Broadband and short-period stations
that distribute within approximately 100 km from the mainshock epicenter are incorporated, which covers the source
region well. The average distance between stations is about
10–20 km (Fig. S1). This selection of stations is similar to that
used by Ross, Idini, et al. (2019) and Shelly (2020). We apply
Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

PALM from 4 July to 16 July 2019 enabling direct comparison
with the Ross, Idini, et al. (2019) and Shelly (2020) catalogs.

Results and Discussion
Phase-picking results
Phase picking is the fundamental step for event detection and
location in the PAL architecture. We test the PAL picker on the
PAL-recalled SCSN events and use SCSN picks as a reference,
which contains about 100,000 P and S pick pairs. We made a
detailed comparison between PAL, STA/LTA, and the kurtosis
picker picking results. Here, both STA/LTA and the kurtosis
picker pick the peak time in the characteristic functions, as
defined by equations (1) and (2), respectively. The choice of
channel is also kept the same with PAL picker: pick P arrivals
on Z-vertical velocity waveforms and S arrivals on the east–
north-horizontal energy. The picking operation is performed
over a ±1 s time-window reference to the SCSN arrival times.
We first compare the distribution of picking deviation (dt)
for the three pickers (Fig. 5a). The phase-detection accuracy is
defined as the ratio of picks with dt < 0.5 s to the total number,
which measures the stability of a picker. The phase-picking
precision is expressed as the mean ± standard deviation (st.
dev.) of the detected phases, whereby the mean value evaluates
the systematic picking deviation and the st. dev. evaluates the
picking concentration. As shown in Figure 5a, the PAL picker
outperforms STA/LTA and the kurtosis picker for both P and S
picks, being stable in detection and precise in picking and having little systematic deviation. In contrast, STA/LTA tends to
pick ahead of SCSN and has low picking precision. This bias is
more serious for S waves, which has a low SNR. The kurtosis
picker has high picking precision, but it results in lagged picks,
which has also been reported by previous studies (Baillard et al.,
2013; Ross and Ben-Zion, 2014). Further improvement can be
made with AI methods (Zhu and Beroza, 2018; Zhou et al.,
2019; Mousavi et al., 2020), especially for the S-wave picking.
However, as stated in the Introduction, the generalization of AI
methods is still a problem and needs further investigation, but
this is out of the scope of this article.
We further explore the performance of STA/LTA and the
kurtosis picker with different window lengths (Fig. 5b,c), which
illustrates the advantage in PAL picker because it combines the
strengths of the two traditional pickers. In P picking (Fig. 5b),
STA/LTA has higher detection ability and picking precision
than kurtosis, under most combinations of window lengths.
For the STA/LTA method, the mean dt drops with increasing
Δt STA , and the best performance is obtained with Δt STA  0:4 s
and Δt LTA  2 s. When picking Sarrivals (Fig. 5c), the kurtosis
picker is more robust to different window lengths and has significantly higher picking precision compared with STA/LTA;
however, the kurtosis picks are consistently later than the
SCSN picks by about 0.1 s, which is caused by the emergent
arrival of S wave. Though the S-wave initial arrival shows up
as a peak in the kurtosis function, the growing amplitude
Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

419

## PDF page 8

(a)

afterward leads to a larger kurtosis amplitude (e.g., Fig. 2 and
Figs. S3–S7). On the other hand, STA/LTA gives consistent early
picking when Δt STA > 0:5 s. Thus, the STA/LTA and long-window kurtosis provide a stable constraint on S-arrival times.
Based on this constraint, the PAL picker utilizes short-window
kurtosis to reveal a more emergent change in amplitude, without
sacrificing the picking stability.

Detection results
We evaluate the detection performance of PALM by comparing with the public SCSN catalog (Hutton et al., 2010;
Hauksson et al., 2020) and the catalogs of Ross, Idini, et al.
(2019) and Shelly (2020).
We first compare the number of detections in the source
area (117.28°–117.8° W and 35.49°–36.01° N). PAL detected
27,024 events, ∼80% more than that in the SCSN catalog,
showing higher detection ability (Fig. 6a). The relocated
MESS catalog contains 59,159 events, a comparable number
to that in Ross, Idini, et al. (2019) and more than 1.5 times
that in Shelly (2020) (Fig. 6b). Ross, Idini, et al. (2019)
employed templates from 4 July to 24 July 2019, which is
eight days more than that used by Shelly (2020) and this
study. We also measure the recall rate of PALM catalog and
the catalogs of Ross, Idini, et al. (2019) and Shelly (2020) on
the SCSN catalog to estimate the detection completeness,
which results in 90.05%, 94.83%, and 93.53% recall rate for
the three catalogs, respectively. A slightly higher recall rate
for the catalogs of Ross, Idini, et al. (2019) and Shelly (2020)
is reasonable because they use the SCSN catalog as a template,
and the matched filter tends to recall template events themselves (i.e., self-detection). Most of the missed events come
420

(c)

(b)

Seismological Research Letters

Figure 5. (a) Phase-picking performance of the PAL, STA/LTA, and
kurtosis algorithms are evaluated as deviations from the
Southern California Seismic Network (SCSN) picks and plotted as
histograms using slash-filled, gray-filled, and blank bars,
respectively. Detection accuracy is defined as the ratio of picks
with an absolute deviation of 0.5 s. Phase-picking precision is
presented by the mean ± standard deviation (st. dev.; s) value for
the detected phases. (b) P-wave detection accuracy and picking
precision for different window lengths. Solid lines with dot, triangle, and square markers denote STA/LTA with the long window length set to 2, 4, and 6 s, respectively. Dashed lines with
circle marker denote picking result by kurtosis picker. In the upper
panel, blue and red lines plot phase-detection accuracy assuming
a maximum picking deviation (dt) of 0.5 and 0.2 s, respectively. In
the lower panel, blue and red lines plot mean and st. dev. values
of picking deviation, respectively. Adopted parameters are
highlighted by yellow-filled dots. Panel (c) is the same as in panel
(b), but for S pick. The color version of this figure is available only
in the electronic edition.

from a poor event connection in the relocation process. It
is worth noting that the detection number by MFT depends
on the association process as well (see the MESS Relocation
section), which determines the robustness in relocation.
Thus, a small difference in the number of events can be
neglected in evaluating the quality of the catalog.
The frequency–magnitude distribution is compared in
Figure 6 to examine the consistency along the magnitude
dimension. The SCSN catalog presents a significant b-value
change for events between M L 1–3.4 and M L 3.5–6, which violates the Gutenberg–Richter law (Gutenberg and Richter,
1944), indicating incompleteness for events smaller than M L
3.4. This bias does not exist in the PAL catalog, which provides
www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 9

(a)

(b)

(c)

MESS
Ross et al. (2019)

PAL

Shelly

SCSN

(2020)

Figure 6. (a) Comparison of frequency–magnitude distribution (FMD). PAL and SCSN catalogs are
plotted with yellow and blue symbols, respectively. Cumulated and noncumulative distribution are
plotted as circles and triangles, respectively. Panel (b) is the same as in panel (a), but for the MFTdetected catalogs: MESS, Ross, Idini, et al. (2019), and Shelly (2020), which are plotted as red,
green, and cyan symbols, respectively. (c) Seismic rate comparison. Results from different catalogs
are plotted in the same colors as panels (a,b). Significant events (ML >4.5) are marked by yellow
asterisks. The color version of this figure is available only in the electronic edition.

a better estimation for b-value (Wiemer and Wyss, 2000;
Woessner and Wiemer, 2005). After the matched filter, the
complete magnitude of the catalog of Ross, Idini, et al. (2019)
is pushed to ∼0.5 under maximum curvature criteria (Wiemer
and Wyss, 2000), but it is obvious that the bias between M L 0.5
and 2.0 still exists, which may alter further analysis on b-value.
This problem does not exist in the result by MESS and Shelly
(2020), although MESS shows much higher detectability. Thus,
the quality of template catalog determines the matched-filter
result, and the PALM architecture renders good matched-filter
performance.
The temporal variation of the detection rate is compared in
Figure 6c to examine the temporal consistency. Expected temporal behaviors of an early aftershock sequence include
(1) abrupt increase immediately after a significant event and
geometrical decrease further afterward, as described by the
Omori’s law (Utsu, 1961, 1970), and (2) consistent overall seismicity rate over a short period (16 days, in this study), although
some possible fluctuations may be included. However, the
Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

initial detections, that is, the
SCSN and PAL catalogs, show
systematic bias (Fig. 6c and
Fig. S8): the SCSN catalog
shows an artificial drop in
the detection rate after 13
July 2019. This phenomenon
is not reflected by other catalogs; thus, it reflects some temporal detection issue of the
SCSN catalog. The PAL catalog
does not show a sharp seismic
activity increase after the major
events, that is, the M w 6.4 foreshock and the M w 7.1 mainshock, indicating a magnitude
completeness change during
intensive seismic activities
right after major events. After
MFT augmentation, the detection rate in MESS shows a sudden increase after large events
(Fig. 6c). This abrupt increase
can also be seen in the catalog
of Shelly (2020), yet it is not
present in the catalog of Ross,
Idini, et al. (2019) after the
mainshock.

Location results
The location of the PAL and
SCSN catalogs is compared
in Figure 7. The PAL +
HypoDD catalog qualitatively
shows a similar level of location clustering and lineation as
the SCSN catalog, which is more concentrated than the
HYPOINVERSE catalog (Fig. 7a), but the PAL cross section
does not show concentration at certain depths as in the
SCSN catalog (Fig. 7c and Fig. S10), which is a common artifact
in the absolute location with 1D velocity model. The PAL +
HypoDD relocation (Fig. 7b) clearly outlines basic fault structures in RC, for example, the orthogonal subfaults cutting the
northwest-striking main fault and the two branches in the
southeast side. In comparison with the SCSN catalog, the relocated PAL catalog recovers more detailed and complete fault
geometrical structure features due to the abundance of detections. This also leads to more robust matched-filter detection
throughout the study region, especially for the southeast end of
the mainshock rupture, for which seismicity in the SCSN catalog is relatively sparse (Fig. 7c).
The relocated MFT catalogs, that is, the MESS catalog and
the catalogs of Ross, Idini, et al. (2019) and Shelly (2020), are
shown in the same manner in Figure 8. Detailed fault
Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

421

## PDF page 10

structures are consistently revealed by the three MFT catalogs,
including the location and strikes of secondary faults
perpendicular to the main fault, the deep clusters on Garlock
fault, and the complex swarm in the northwest end of the coseismic rupture. Owing to the high-resolution CC-based differential
time measurement, a comparable resolution is achieved by the
three MFT catalogs. The relocation resolution of the MESS catalog and the catalog of Shelly (2020) appears to be higher than
that of Ross, Idini, et al. (2019), which may be caused by the
difference in the relocation algorithms, that is, Ross, Idini, et al.
(2019) is from GrowClust (Trugman and Shearer, 2017), but
MESS and Shelly (2020) are by HypoDD (Waldhauser,
2001). The HypoDD algorithm tends to remove events showing
in-consistent arrivals with other events, whereas the GrowClust
algorithm treats them as low-weighted events.
Despite the consistency of general patterns of the three catalogs, the depth distribution of these catalogs varies. The most
significant difference occurs in the northwest side of the mainshock epicenter (∼15–25 km along-profile distance, Fig. 8), in
which large coseismic slip is observed at the shallow portion
(∼0–5 km, (Ross, Idini, et al., 2019; Goldberg et al., 2020; Jin
and Fialko, 2020). In such an area, we expect to see a deficit
in aftershock activity (Wetzler et al., 2018), and the MESS catalog
fits this pattern better than the results of Ross, Idini, et al. (2019)
or Shelly (2020). This may come from the difference in phase
association and the absolute location process, which are not
included in the research of Ross, Idini, et al. (2019) or Shelly
(2020); thus it serves as a good case to show the advantage of
a complete detection and location workflow. Differences also
exist in the relocation process; though both start from SCSN
locations, the catalogs of Ross, Idini, et al. (2019) and Shelly
422

Seismological Research Letters

Figure 7. Location comparison for template events. Plot locations
of catalogs obtained by (a) PAL + HYPOINVERSE, (b) PAL +
HypoDD, and (c) SCSN, respectively. Earthquakes are plotted in
dots color coded by their hypocentral depths with the marker size
scaled with magnitude. Cross sections are plotted in blue-dashed
squares. Profiles of catalog depth distribution along profile OO′
are denoted as blue dots. The color version of this figure is
available only in the electronic edition.

(2020) deviate from each other for ∼2 km in the depth distribution (Fig. 8 and Fig. S10). Again, this is partly due to different
relocation methods because GrowClust does not explicitly constrain the separation distance of event pairs. Such a deviation can
be enlarged with different template locations. However, in the
relocation process, we are keeping track of the consistency
between MESS and the relocated templates (i.e., PAL +
HypoDD), so no systematic deviations are introduced. Thus,
the small differences between the MESS catalog and the catalogs
of Ross, Idini, et al. (2019) and Shelly (2020) reflect the uncertainty introduced by the relocation method and starting locations
of template events.

Conclusion
We developed an earthquake detection and location architecture
that sequentially perform PALM techniques. The design of
PALM is specified to directly apply to continuous seismograms
and to produce high-resolution catalogs, while not requiring a
reference catalog. This architecture is particularly useful for
large-scale seismicity monitoring networks without detailed visual inspection, such as the on-building seismicity monitoring
network in the Sichuan–Yunnan Province of China (Wu et al.,
www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 11

2019). We adopted PALM to the 2019 Ridgecrest aftershock
sequence and compared the catalog with several published
catalogs. The comparison demonstrates the following:
1. The PAL picker realizes robust phase detection and high
picking precision, with an optimal combination of STA/
LTA and the kurtosis algorithm.
2. PAL achieves high detectability and accurate location,
which serves as a sound foundation for the subsequent
matched-filter detection.
3. MESS augments the PAL detections and gives high-resolution relocation with cross correlation.
4. PALM can recover an unbiased and fine fault structure
from continuous data.

Data and Resources
Seismic data and phase arrivals used in this study were downloaded
from Southern California Earthquake Data Center (SCEDC) at
https://scedc.caltech.edu/ (last accessed November 2020). The software phase picking, phase association, location, and matched-filter
(PALM) techniques, that is, PAL and MESS, were developed with
Python, Obspy, Numpy, Scipy, and Pytorch. PAL and MESS are accessible via GitHub: PAL (DOI: 10.5281/zenodo.4916097; https://
github.com/YijianZhou/PAL, last accessed July 2021) and MESS
(DOI: 10.5281/zenodo.4916100; https://github.com/YijianZhou/
MESS, last accessed July 2021). The supplemental material accompanying this article includes details of the principal component analysis
(PCA) polarization analysis used in the PAL picker, the efficiency in
each step of PALM, and figures that help to validate the detection and
location result in Ridgecrest. The detected and relocated seismic catalog by PALM can also be accessed from the supplemental material.
Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

Figure 8. Location comparison for MFT catalogs. Markers have the
same meaning as Figure 7. (a) MESS HypoDD, (b) Shelly (2020),
and (c) Ross, Idini, et al. (2019). The color version of this figure is
available only in the electronic edition.

Declaration of Competing Interests
The authors acknowledge that there are no conflicts of interest
recorded.

Acknowledgments
The authors thank Jun Li, Jian Piao, Hao Zhang, Yuan Yao, Weifan Lu,
and Long Zhang for their active applications and suggestions on phase
picking, phase association, location, and matched-filter (PALM) techniques. This research is supported jointly by the Nature Science
Foundation of China (NSFC) projects (Grant Numbers U2039204,
42074046, and 41774067), Science for Earthquake Resilience (Grant
Number XH20082Y), U.S. National Science Foundation (Award
Number 1941719), and University of California at Riverside.

References
Allen, R. V. (1978). Automatic earthquake recognition and timing
from single traces, Bull. Seismol. Soc. Am. 68, no. 5, 1521–1532.
Baillard, C., W. C. Crawford, V. Ballu, C. Hibert, and A. Mangeney
(2013). An automatic kurtosis-based P- and S-phase picker
designed for local seismic networks, Bull. Seismol. Soc. Am.
104, no. 1, 394–409, doi: 10.1785/0120120347.
Boore, D. M. (1989). The Richter scale: Its development and use for
determining earthquake source parameters, Tectonophysics 166,
no. 1, 1–14, doi: 10.1016/0040-1951(89)90200-X.
Chai, C., M. Maceira, H. J. Santos-Villalobos, S. V. Venkatakrishnan,
M. Schoenball, W. Zhu, G. C. Beroza, C. Thurber, and E. C. Team
Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

423

## PDF page 12

(2020). Using a deep neural network and transfer learning to
bridge scales for seismic phase picking, Geophys. Res. Lett. 47,
no. 16, e2020GL088651, doi: 10.1029/2020GL088651.
Chen, C., and A. A. Holland (2016). PhasePApy: A robust pure
Python package for automatic identification of seismic
phases, Seismol. Res. Lett. 87, no. 6, 1384–1396, doi: 10.1785/
0220160019.
Chen, X., P. M. Shearer, and R. E. Abercrombie (2012). Spatial migration of earthquakes within seismic clusters in southern California:
Evidence for fluid diffusion, J. Geophys. Res. 117, no. B4, doi:
10.1029/2011JB008973.
Cochran, E. S., E. Wolin, D. E. McNamara, A. Yong, D. Wilson, M.
Alvarez, N. van der Elst, A. McClain, and J. Steidl (2020). The U.S.
Geological Survey’s rapid seismic array deployment for the 2019
Ridgecrest earthquake sequence, Seismol. Res. Lett. 91, no. 4, 1952–
1960, doi: 10.1785/0220190296.
Di Luccio, F., G. Ventura, R. Di Giovambattista, A. Piscini, and F. R.
Cinti (2010). Normal faults and thrusts reactivated by deep fluids:
The 6 April 2009 Mw 6.3 L’Aquila earthquake, central Italy, J.
Geophys. Res. 115, no. B6, doi: 10.1029/2009JB007190.
Frémont, M.-J., and S. D. Malone (1987). High precision relative locations of earthquakes at Mount St. Helens, Washington, J. Geophys.
Res. 92, no. B10, 10,223–10,236, doi: 10.1029/JB092iB10p10223.
Geiger, L. (1912). Probability method for the determination of earthquake epicenters from the arrival time only, Bull. St. Louis Univ.
8, no. 1, 56–71.
Gibbons, S. J., and F. Ringdal (2006). The detection of low
magnitude seismic events using array-based waveform correlation,
Geophys. J. Int. 165, no. 1, 149–166, doi: 10.1111/j.1365246X.2006.02865.x.
Goldberg, D. E., D. Melgar, V. J. Sahakian, A. M. Thomas, X. Xu, B. W.
Crowell, and J. Geng (2020). Complex rupture of an immature
fault zone: A simultaneous kinematic model of the 2019
Ridgecrest, CA earthquakes, Geophys. Res. Lett. 47, no. 3,
e2019GL086382, doi: 10.1029/2019GL086382.
Gutenberg, B., and C. F. Richter (1944). Frequency of earthquakes in
California, Bull. Seismol. Soc. Am. 34, no. 4, 185–188.
Hauksson, E., C. Yoon, E. Yu, J. R. Andrews, M. Alvarez, R. Bhadha, and
V. Thomas (2020). Caltech/USGS Southern California Seismic
Network (SCSN) and Southern California Earthquake Data
Center (SCEDC): Data availability for the 2019 Ridgecrest sequence,
Seismol. Res. Lett. 91, no. 4, 1961–1970, doi: 10.1785/0220190290.
Hayes, G. P., D. J. Wald, and R. L. Johnson (2012). Slab1.0: A threedimensional model of global subduction zone geometries, J.
Geophys. Res. 117, no. B1, doi: 10.1029/2011jb008524.
Husen, S., and J. Hardebeck (2010). Earthquake Location Accuracy,
Community Online Resource for Statistical Seismicity Analysis,
doi: 10.5078/corssa-55815573.
Hutton, K., J. Woessner, and E. Hauksson (2010). Earthquake monitoring in southern California for seventy-seven years (1932–2008), Bull.
Seismol. Soc. Am. 100, no. 2, 423–446, doi: 10.1785/0120090130.
Hutton, L. K., and D. M. Boore (1987). The ML scale in southern
California, Bull. Seismol. Soc. Am. 77, no. 6, 2074–2094.
Jin, Z., and Y. Fialko (2020). Finite slip models of the 2019 Ridgecrest
earthquake sequence constrained by space geodetic data and aftershock locations, Bull. Seismol. Soc. Am. 110, no. 4, 1660–1679, doi:
10.1785/0120200060.

424

Seismological Research Letters

Johnson, C. E., A. G. Lindh, and B. F. Hirshorn (1997). Robust
regional phase association, U.S. Geol. Surv. Open-File Rept. 94621, doi: 10.3133/ofr94621.
Kato, A., J. I. Fukuda, S. Nakagawa, and K. Obara (2016). Foreshock
migration preceding the 2016 Mw 7.0 Kumamoto earthquake,
Japan, Geophys. Res. Lett. 43, no. 17, 8945–8953, doi: 10.1002/
2016GL070079.
Klein, F. W. (2002). User’s guide to HYPOINVERSE-2000, a Fortran
program to solve for earthquake locations and magnitudes, U.S.
Geol. Surv. Open-File Rept. 2331-1258.
Kohler, M. D., H. Magistrale, and R. W. Clayton (2003). Mantle
heterogeneities and the SCEC reference three-dimensional seismic
velocity model version 3, Bull. Seismol. Soc. Am. 93, no. 2, 757–
774, doi: 10.1785/0120020017.
Liu, M., M. Zhang, W. Zhu, W. L. Ellsworth, and H. Li (2020). Rapid
characterization of the July 2019 Ridgecrest, California, earthquake
sequence from raw seismic data using machine-learning phase picker,
Geophys. Res. Lett. 47, no. 4, e2019GL086189, doi: 10.1029/
2019GL086189.
Lomax, A. (2020). Absolute location of 2019 Ridgecrest seismicity
reveals a shallow Mw 7.1 hypocenter, migrating and pulsing Mw
7.1 foreshocks, and duplex Mw 6.4 ruptures, Bull. Seismol. Soc.
Am. 110, no. 4, 1845–1858, doi: 10.1785/0120200006.
Mendoza, M. M., A. Ghosh, M. S. Karplus, S. L. Klemperer, S. N.
Sapkota, L. B. Adhikari, and A. Velasco (2019). Duplex in the main
Himalayan thrust illuminated by aftershocks of the 2015 Mw 7.8
Gorkha earthquake, Nature Geosci. 12, no. 12, 1018–1022, doi:
10.1038/s41561-019-0474-8.
Mousavi, S. M., W. L. Ellsworth, W. Zhu, L. Y. Chuang, and G. C.
Beroza (2020). Earthquake transformer—An attentive deep-learning model for simultaneous earthquake detection and phase picking,
Nat. Commun. 11, no. 1, 3952, doi: 10.1038/s41467-020-17591-w.
Mousavi, S. M., Y. Sheng, W. Zhu, and G. C. Beroza (2019). STanford
EArthquake Dataset (STEAD): A global data set of seismic
signals for AI, IEEE Access. 7, 179,464–179,476, doi: 10.1109/
ACCESS.2019.2947848.
Patton, J. M., M. R. Guy, H. M. Benz, R. P. Buland, B. K. Erickson, and
D. S. Kragness (2016). Hydra—The National earthquake information center’s 24/7 seismic monitoring, analysis, catalog production,
quality analysis, and special studies tool suite, U.S. Geol. Surv. Rept.
2016-1128, doi: 10.3133/ofr20161128.
Peng, Z., and P. Zhao (2009). Migration of early aftershocks following
the 2004 Parkfield earthquake, Nature Geosci. 2, no. 12, 877–881,
doi: 10.1038/ngeo697.
Richter, C. F. (1935). An instrumental earthquake magnitude scale,
Bull. Seismol. Soc. Am. 25, no. 1, 1–32.
Ross, Z. E., and Y. Ben-Zion (2014). Automatic picking of direct P, S
seismic phases and fault zone head waves, Geophys. J. Int. 199,
no. 1, 368–381, doi: 10.1093/gji/ggu267.
Ross, Z. E., E. Hauksson, and Y. Ben-Zion (2017). Abundant off-fault
seismicity and orthogonal structures in the San Jacinto fault zone,
Sci. Adv. 3, no. 3, e1601946, doi: 10.1126/sciadv.1601946.
Ross, Z. E., B. Idini, Z. Jia, O. L. Stephenson, M. Zhong, X. Wang, Z.
Zhan, M. Simons, E. J. Fielding, S. H. Yun, et al. (2019).
Hierarchical interlocked orthogonal faulting in the 2019
Ridgecrest earthquake sequence, Science 366, no. 6463, 346–
351, doi: 10.1126/science.aaz0109.

www.srl-online.org

•

Volume 93

•

Number 1

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

•

January 2022

## PDF page 13

Ross, Z. E., D. T. Trugman, E. Hauksson, and P. M. Shearer (2019).
Searching for hidden earthquakes in southern California, Science
364, no. 6442, 767–771, doi: 10.1126/science.aaw6888.
Scholz, C. H. (1968). The frequency–magnitude relation of microfracturing in rock and its relation to earthquakes, Bull. Seismol. Soc.
Am. 58, no. 1, 399–415.
Schorlemmer, D., and S. Wiemer (2005). Microseismicity data forecast rupture area, Nature 434, no. 7037, 1086–1086, doi: 10.1038/
4341086a.
Shelly, D. R. (2020). A high-resolution seismic catalog for the initial
2019 Ridgecrest earthquake sequence: Foreshocks, aftershocks,
and faulting complexity, Seismol. Res. Lett. 91, no. 4, 1971–
1978, doi: 10.1785/0220190309.
Shelly, D. R., G. C. Beroza, and S. Ide (2007). Non-volcanic tremor
and low-frequency earthquake swarms, Nature 446, no. 7133,
305–307, doi: 10.1038/nature05666.
Shelly, D. R., W. L. Ellsworth, and D. P. Hill (2016). Fluid-faulting
evolution in high definition: Connecting fault structure and
frequency–magnitude variations during the 2014 Long Valley
caldera, California, earthquake swarm, J. Geophys. Res. 121,
no. 3, 1776–1795, doi: 10.1002/2015JB012719.
Spada, M., T. Tormann, S. Wiemer, and B. Enescu (2013). Generic
dependence of the frequency-size distribution of earthquakes
on depth and its relation to the strength profile of the crust,
Geophys. Res. Lett. 40, no. 4, 709–714, doi: 10.1029/
2012gl054198.
Sun, J., H. Yue, Z. Shen, L. Fang, Y. Zhan, and X. Sun (2018). The 2017
Jiuzhaigou earthquake: A complicated event occurred in a Young
fault system, Geophys. Res. Lett. 45, no. 5, 2230–2240, doi: 10.1002/
2017gl076421.
Trugman, D. T., and P. M. Shearer (2017). GrowClust: A hierarchical
clustering algorithm for relative earthquake relocation, with application to the Spanish Springs and Sheldon, Nevada, earthquake
sequences, Seismol. Res. Lett. 88, no. 2A, 379–391, doi: 10.1785/
0220160188.
Turin, G. (1960). An introduction to matched filters, IRE
Trans. Inform. Theor. 6, no. 3, 311–329, doi: 10.1109/
TIT.1960.1057571.
Uhrhammer, R. A., M. Hellweg, K. Hutton, P. Lombard, A. W.
Walters, E. Hauksson, and D. Oppenheimer (2011). California
Integrated Seismic Network (CISN) local magnitude determination in California and vicinity, Bull. Seismol. Soc. Am. 101,
no. 6, 2685–2693, doi: 10.1785/0120100106.
Utsu, T. (1961). A statistical study on the occurrence of aftershocks,
Geophys. Mag. 30, no. 4, 521–605.
Utsu, T. (1970). Aftershocks and earthquake statistics (1): Some
parameters which characterize an aftershock sequence and their
interrelations, J. Faculty Sci., Hokkaido Univ. Ser. 7, Geophys. 3,
no. 3, 129–195.
Waldhauser, F. (2001). HypoDD—A program to compute doubledifference hypocenter locations, U.S. Geol. Surv. Open-File Rept.
01-113, 25 pp.
Waldhauser, F., and W. L. Ellsworth (2000). A double-difference
earthquake location algorithm: Method and application to the
northern Hayward fault, California, Bull. Seismol. Soc. Am. 90,
no. 6, 1353–1368, doi: 10.1785/0120000006.

Volume 93

•

Number 1

•

January 2022

•

www.srl-online.org

Waldhauser, F., and W. L. Ellsworth (2002). Fault structure and
mechanics of the Hayward fault, California, from doubledifference earthquake locations, J. Geophys. Res. 107, no. B3,
ESE 3-1–ESE 3-15, doi: 10.1029/2000jb000084.
Wetzler, N., T. Lay, E. E. Brodsky, and H. Kanamori (2018).
Systematic deficiency of aftershocks in areas of high coseismic slip
for large subduction zone earthquakes, Sci. Adv. 4, no. 2, eaao3225,
doi: 10.1126/sciadv.aao3225.
White, M. C. A., Y. Ben-Zion, and F. L. Vernon (2019). A detailed
earthquake catalog for the San Jacinto fault-zone region in
southern California, J. Geophys. Res. 124, no. 7, 6908–6930, doi:
10.1029/2019JB017641.
Wiemer, S., and M. Wyss (2000). Minimum magnitude of completeness in earthquake catalogs: Examples from Alaska, the western
United States, and Japan, Bull. Seismol. Soc. Am. 90, no. 4,
859–869, doi: 10.1785/0119990114.
Withers, M., R. Aster, C. Young, J. Beiriger, M. Harris, S. Moore, and J.
Trujillo (1998). A comparison of select trigger algorithms for automated global seismic phase and event detection, Bull. Seismol. Soc.
Am. 88, no. 1, 95–106.
Woessner, J., and S. Wiemer (2005). Assessing the quality of earthquake catalogues: Estimating the magnitude of completeness
and its uncertainty, Bull. Seismol. Soc. Am. 95, no. 2, 684–698,
doi: 10.1785/0120040007.
Wu, Z., X. Zhang, and K. Sun (2019). China Seismic Experiment Site:
Scientific challenges, Acta Geol. Sinica 93, no. S1, 273–273, doi:
10.1111/1755-6724.14084.
Yue, H., Z. E. Ross, C. Liang, S. Michel, H. Fattahi, E. Fielding, A.
Moore, Z. Liu, and B. Jia (2017). The 2016 Kumamoto Mw =
7.0 earthquake: A significant event in a fault–volcano system, J.
Geophys. Res. 122, no. 11, 9166–9183, doi: 10.1002/2017jb014525.
Yue, H., Y. Zhou, S. Zhou, Y. Huang, M. Li, L. Zhou, and Z. Liu (2018).
The 2017 Jiuzhaigou earthquake aftershock-monitoring experimental network: Network design and signal enhancement algorithm,
Seismol. Res. Lett. 89, no. 5, 1671–1679, doi: 10.1785/0220180046.
Zhang, M., W. L. Ellsworth, and G. C. Beroza (2019). Rapid earthquake association and location, Seismol. Res. Lett. 90, no. 6,
2276–2284, doi: 10.1785/0220190052.
Zhou, S., Z. Xu, and X. Chen (2001). Analysis on the source characteristics of the 1997 Jiashi Swarm, western China, Chin. J. Geophys.
44, no. 5, 654–662.
Zhou, Y., H. Yue, Q. Kong, and S. Zhou (2019). Hybrid event
detection and phase-picking algorithm using convolutional
and recurrent neural networks, Seismol. Res. Lett. 90, no. 3,
1079–1087, doi: 10.1785/0220180319.
Zhu, L., Z. Peng, J. McClellan, C. Li, D. Yao, Z. Li, and L. Fang (2019).
Deep learning for seismic phase detection and picking in the aftershock zone of 2008 Mw 7.9 Wenchuan earthquake, Phys. Earth
Planet. In. 293, 106,261, doi: 10.1016/j.pepi.2019.05.004.
Zhu, W., and G. C. Beroza (2018). PhaseNet: A deep-neural-networkbased seismic arrival-time picking method, Geophys. J. Int. 216,
no. 1, 261–273, doi: 10.1093/gji/ggy423.

Manuscript received 27 April 2021
Published online 1 September 2021

Seismological Research Letters

Downloaded from pubs.​geoscienceworld.​org/​ssa/​srl/​article-pdf/​93/​1/​413/​5492529/​srl-2021111.​1.​pdf by China Univ of Geosciences Library Wuhan user on 12 September 2026

425
