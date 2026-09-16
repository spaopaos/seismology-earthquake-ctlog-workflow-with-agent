# An AI Agent for Fully Automated Multi-Omic Analyses

Source: zhou-2024-autoba.pdf
Extraction: pdftotext; physical PDF page numbers, starting at 1.
Text-layer extraction does not reproduce figures and may imperfectly render formulas or tables.

## PDF page 1

RESEARCH ARTICLE
www.advancedscience.com

An AI Agent for Fully Automated Multi-Omic Analyses
Juexiao Zhou, Bin Zhang, Guowei Li, Xiuying Chen, Haoyang Li, Xiaopeng Xu,
Siyuan Chen, Wenjia He, Chencheng Xu, Liwei Liu,* and Xin Gao*

With the fast-growing and evolving omics data, the demand for streamlined
and adaptable tools to handle bioinformatics analysis continues to grow. In
response to this need, Automated Bioinformatics Analysis (AutoBA) is
introduced, an autonomous AI agent designed explicitly for fully automated
multi-omic analyses based on large language models (LLMs). AutoBA
simpliﬁes the analytical process by requiring minimal user input while
delivering detailed step-by-step plans for various bioinformatics tasks.
AutoBA’s unique capacity to self-design analysis processes based on input
data variations further underscores its versatility. Compared with online
bioinformatic services, AutoBA oﬀers multiple LLM backends, with options for
both online and local usage, prioritizing data security and user privacy. In
comparison to ChatGPT and open-source LLMs, an automated code repair
(ACR) mechanism in AutoBA is designed to improve its stability in automated
end-to-end bioinformatics analysis tasks. Moreover, diﬀerent from the
predeﬁned pipeline, AutoBA has adaptability in sync with emerging
bioinformatics tools. Overall, AutoBA represents an advanced and convenient
tool, oﬀering robustness and adaptability for conventional multi-omic
analyses.

J. Zhou, B. Zhang, X. Chen, H. Li, X. Xu, S. Chen, W. He, C. Xu, X. Gao
Computer Science Program
Computer, Electrical and Mathematical Sciences and Engineering
Division
King Abdullah University of Science and Technology (KAUST)
Thuwal 23955-6900, Kingdom of Saudi Arabia
E-mail: xin.gao@kaust.edu.sa
J. Zhou, B. Zhang, X. Chen, H. Li, X. Xu, S. Chen, W. He, C. Xu, X. Gao
Center of Excellence on Smart Health
King Abdullah University of Science and Technology
Thuwal 23955-6900, Kingdom of Saudi Arabia
G. Li
Laboratory of Health Intelligence
Huawei Technologies Co., Ltd
Shenzhen 210000, China
L. Liu
Advanced Computing and Storage Laboratory
Central Research Institute
2012 Laboratories, Huawei Technologies Co., Ltd
Nanjing, Jiangsu 210000, China
E-mail: liuliwei5@huawei.com
The ORCID identiﬁcation number(s) for the author(s) of this article
can be found under https://doi.org/10.1002/advs.202407094
© 2024 The Author(s). Advanced Science published by Wiley-VCH
GmbH. This is an open access article under the terms of the Creative
Commons Attribution License, which permits use, distribution and
reproduction in any medium, provided the original work is properly cited.

DOI: 10.1002/advs.202407094

Adv. Sci. 2024, 11, 2407094

2407094 (1 of 15)

1. Introduction

Bioinformatics is an interdisciplinary
ﬁeld that encompasses computational,
statistical, and biological approaches to
analyze, understand and interpret complex biological data.[1–3] With the rapid
growth of gigabyte-sized biological data
generated from various high-throughput
technologies, bioinformatics has become
an essential tool for researchers to make
sense of these massive datasets and extract
meaningful biological insights. The applications of bioinformatics typically cover
diverse ﬁelds such as genome analysis,[4,5]
structural bioinformatics,[6–7] systems
biology,[8] data and text mining,[9–10]
phylogenetics,[11–12]
and
population
analysis,[13] which has further enabled
signiﬁcant advances in personalized
medicine[14] and drug discovery.[15]
In broad terms, bioinformatics could
be categorized into two primary domains: the development of innovative
algorithms to address various biological challenges,[16–20] and
the application of established tools to analyze extensive biological datasets,[21,22] especially high-throughput sequencing
data. Developing new bioinformatics software requires a substantial grasp of biology and programming expertise. Alongside the development of novel computational methods, one
of the most prevalent applications of bioinformatics is the
investigation of biological data using the existing tools and
pipelines,[23,24] which typically involves a sequential, ﬂow-based
analysis of omics data, encompassing variety types of datasets
like whole genome sequencing (WGS),[25] whole exome sequencing (WES), RNA sequencing (RNA-seq),[26] single-cell RNA-seq
(scRNA-Seq),[27] transposase-accessible chromatin with sequencing (ATAC-Seq),[28] ChIP-seq,[29] and spatial transcriptomics.[30]
For example, the conventional analytical framework for bulk
RNA-seq involves a meticulously structured sequence of computational steps.[31] This intricate pipeline reveals its complexity through a series of carefully orchestrated stages. It
begins with quality control,[32] progresses to tasks such as
adapter trimming[33] and the removal of low-quality reads, and
then moves on to critical steps like genome or transcriptome
alignment.[34] Furthermore, it extends to some advanced tasks,
including the identiﬁcation of splice junctions,[35] quantiﬁcation through read counting,[36] and the rigorous examination
of diﬀerential gene expression.[37] Moreover, the pipeline delves
into the intricate domain of alternative splicing[38] and isoform

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

## PDF page 2

www.advancedscience.com

analysis.[39] This progressive journey ultimately ends in downstream tasks like the exploration of functional enrichment,[40]
providing a comprehensive range of analytical pursuits. Compared to bulk RNA-seq, ChIP-seq involves distinct downstream tasks, such as peak calling,[41] motif discovery,[42] peak
annotation[43] and so on. In summary, the analysis of diﬀerent
types of omics data requires professional skills and a comprehensive comprehension of the corresponding ﬁeld, particularly for
customized data analysis. Moreover, the methods and pipelines
might vary across diﬀerent bioinformaticians and they even may
evolve with the development of more advanced algorithms.
Meanwhile, online semi-automatic bioinformatics analysis
platforms are currently in vogue,[44] such as iDEP,[45] ICARUS[46]
and STellaris.[47] However, they often necessitate the uploading of
either raw data or pre-processed statistics by users, which could
potentially give rise to additional privacy concerns and data leakage risks.[48]
In the context described above, the bioinformatics community grapples with essential concerns regarding the standardization, portability, and reproducibility of analysis pipelines.[49–51]
Moreover, achieving proﬁciency in utilizing these pipelines for
data analysis demands additional training, posing challenges for
many wet lab researchers due to its potential complexity and
time-consuming nature. Even dry-lab researchers may ﬁnd the
repetitive process of running and debugging these pipelines to be
quite tedious.[52] Meanwhile, bioinformatics data analysis training incurs substantial costs. The elevated expenses associated
with training in bioinformatics data analysis could be attributed
to the highly specialized nature of the ﬁeld, the need for multimodal data analysis, the evolution of technologies, restricted
computing resources, the expense of training materials and tools,
as well as the operational costs of training institutions. These
factors collectively contribute to the high cost of bioinformatics
training.[53] Consequently, there is a growing anticipation within
the community for the development of a more user-friendly, lowcode, multi-functional, automated, and natural language-driven
intelligent tool tailored for end-to-end bioinformatics analysis.
Such a tool has the potential to generate signiﬁcant excitement
and beneﬁt researchers across the ﬁeld.
Over the past few months, the rapid advancement of Large
Language Models (LLMs)[54] has raised substantial expectations
for the enhancement of scientiﬁc research, particularly in the
ﬁeld of biology.[55–57] These advancements hold promise for
applications such as disease diagnosis,[58–61] drug discovery,[62]
and all. In the realm of bioinformatics, LLMs, such as ChatGPT,
also demonstrate immense potential in tasks related to bioinformatics education[63] and code generation.[64] While researchers
have found ChatGPT to be a valuable tool in facilitating bioinformatics research, such as data analysis, there remains a strong
requirement for human intervention in the execution process.
ChatGPT shows sensitivity to the nuances of user queries,
resulting in diverse responses based on the prompts, which is
the reason why prompt engineering is getting huge attention.[65]
Given the specialized nature of bioinformatics tools, ChatGPT is
also susceptible to potential issues, such as misinterpreting parameters, errors in software utilization, and other bugs that may
arise during code generation. Users may encounter the necessity
for ongoing engagement with ChatGPT, involving a continuous
cycle of inquiry, code generation, execution, and debugging to en-

Adv. Sci. 2024, 11, 2407094

2407094 (2 of 15)

sure desired performance. AutoGPT,[66] as a recently developed,
advanced, and experimental open-source autonomous AI agent,
has the capacity to string together LLM-generated “thoughts”
to autonomously achieve user-deﬁned objectives. Nevertheless,
given the intricate and specialized nature of bioinformatics tasks,
such as specialized software, the direct application of AutoGPT
in this ﬁeld still presents signiﬁcant challenges. Notably, it
faces diﬃculties in eﬀectively managing the intricate software
requirements of bioinformatics, encompassing tasks such as
installation, software calls, and parameter settings.
In this study, we introduce Automated Bioinformatics Analysis
(AutoBA), an autonomous AI agent tailored for comprehensive
and conventional multi-omic analyses, as it can be applied to the
analysis of diﬀerent omics datasets. AutoBA simpliﬁes user interactions to just three inputs: data path, data description, and the
ﬁnal objective. This tool autonomously proposes analysis plans,
generates code, executes codes, and conducts subsequent data
analysis by using our well-designed prompts. We implemented
AutoBA as open-source software that oﬀers multiple LLM backends, with options for both online and local usage, prioritizing
data security and user privacy (Figure 1). To show the reliability of
AutoBA, we tested it in a large number of real-world multi-omic
analysis scenarios (Figure 2). AutoBA, serving as an AI agent tailored for bioinformatics data analysis, could address the surging
demand for streamlined multi-omics data analysis, mitigate the
ﬁnancial challenges associated with bioinformatics training, and
cater to diverse customization requirements. Compared with online bioinformatic services, AutoBA oﬀers multiple LLM backends, with options for both online and local usage, prioritizing
data security and user privacy (Table 1). In comparison to ChatGPT and open-source LLMs, we have designed an automated
code repair mechanism in AutoBA to improve its stability in automated end-to-end bioinformatics analysis tasks. Moreover, different from the predeﬁned pipeline, AutoBA has adaptability in
sync with emerging bioinformatics tools. In summary, AutoBA
is the ﬁrst agent of this kind and represents a signiﬁcant leap in
the application of LLMs and automated AI agents within the domain of bioinformatics, highlighting their potential to accelerate
future research in this ﬁeld.

2. Experimental Section
2.1. The Overall Framework Design of AutoBA
AutoBA is the ﬁrst autonomous AI agent tailor-made for conventional multi-omic analyses. As illustrated in Figure 1, conventional bioinformatics typically entails the use of pipelines to
analyze diverse data types such as WGS, WES, RNA-seq, singlecell RNA-seq, ChIP-seq, ATAC-seq, spatial transcriptomics, and
more, all requiring the utilization of various tools. Users are traditionally tasked with selecting the appropriate tools based on their
speciﬁc analysis needs. In practice, this process involves conﬁguring the environment, installing software, writing code, and debugging, which are time-consuming and labor-intensive.
With the advent of AutoBA, this labor-intensive process
is revolutionized. Users are relieved from the burden of
dealing with multiple software packages and need only provide three key inputs in YAML format: the data path (e.g.,
/data/SRR1374921.fasta.gz), data description (e.g., single-end

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 3

www.advancedscience.com

Figure 1. Design of AutoBA. AutoBA stands as the ﬁrst autonomous AI agent meticulously crafted for conventional multi-omic analyses. Remarkably
user-friendly, AutoBA simpliﬁes the analytical process by requiring minimal user input, including data path, data description, and the ﬁnal objective,
while delivering detailed step-by-step plans for various bioinformatics tasks. With these inputs, it autonomously proposes analysis plans, generates code,
executes codes, and conducts subsequent data analysis by using our well-designed prompts. AutoBA was implemented as open-source software that
oﬀers multiple LLM backends, with options for both online and local deployment, prioritizing data security and user privacy and oﬀering a streamlined
and eﬃcient solution for bioinformatics tasks. Step 1 and Step 3 require human intervention, while Step 2 requires no human intervention. Due to the
numerous and complex nature of these speciﬁc items, they are represented with ellipsis to indicate the vast and detailed possibilities that cannot be
fully enumerated in this limited space.

reads in condition A), and the ultimate analysis goal (e.g.,
identify diﬀerentially expressed genes). AutoBA takes over by
autonomously analyzing the data, generating comprehensive
step-by-step plans, composing code for each step, executing the
generated code, and conducting in-depth analysis. Depending
on the complexity and diﬃculty of the tasks, users can expect
AutoBA to complete the tasks within a matter of minutes to a few
hours, all without the need for additional human intervention
(Table 2 and Figure 2).

2.2. Prompt Engineering of AutoBA
To initiate AutoBA, users provide three essential inputs: the data
path, data description, and the previously mentioned analysis ob-

Adv. Sci. 2024, 11, 2407094

2407094 (3 of 15)

jective. AutoBA comprises three distinct phases: the planning
phase, the code generation phase, and the execution phase as
shown in Step 2 of Figure 1. During the planning phase, AutoBA meticulously outlines a comprehensive step-by-step analysis plan. This plan includes details such as the software name
and version to be used at each step, along with guided actions
and speciﬁc sub-tasks for each stage. Subsequently, in the code
generation phase, AutoBA systematically follows the plan and
generates codes for sub-tasks, which entails procedures like conﬁguring the environment, installing the necessary software, and
writing code. Then, in the execution phase, AutoBA executes the
generated code. In light of this workﬂow, AutoBA incorporates
two distinct prompts: one tailored for the planning phase and
the other for the code generation phase. Intensive experiments
have shown that these two sets of prompts are essential for the

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 4

www.advancedscience.com

Figure 2. Method design and evaluation of AutoBA. a) AutoBA workﬂow design and technical details. b) Pie chart indicates the number of all cases used
for validating AutoBA.

proper functioning of AutoBA in automated bioinformatics analysis tasks.
The prompts for both the planning phase and the code generation phase are displayed in the Supporting Information. In
both prompt designs, the term blacklist pertains to the user’s personalized list of prohibited software. The current default blacklist contains several tools that frequently caused errors during
the testing processes. Meanwhile, data list encompasses the inputs necessary for AutoBA, encompassing data paths and data
descriptions. The term current goal serves as the ﬁnal objective

during the planning phase and as the sub-goal in the execution
phase, while history summary encapsulates AutoBA’s memory of
previous actions and information.

2.3. Memory Management of AutoBA
A memory mechanism is incorporated within AutoBA to enable
it to generate code more eﬀectively by drawing from past actions,
thus avoiding unnecessary repetition of certain steps. AutoBA

Table 1. Qualitative comparison of AutoBA against other methods. All methods were conceptually assessed with seven metrics, including userfriendliness, time eﬃciency, diminished human intervention (degree of automation), ease of redevelopment, generality, robustness, and privacy considerations. * denotes a category of methods rather than a speciﬁc one. For instance, Online Webserver refers to platforms like iDEP and ICARUS, and
Open Source LLMs includes models such as Llama2 and CodeLlama.
Methods

Easy to Master

Save Time

Reduced Human
Intervention

Redevelopment

Generalizability

Robustness

AutoBA

✓✓✓

✓✓✓

✓✓✓

✓✓✓

✓✓✓

✓✓✓

✓✓✓

✓

✓

–

✓✓

✓

✓✓

✓✓✓

Conventional
Bioinformatics Tools
Online Webserver∗

Privacy

✓✓

✓✓

–

–

✓

✓

–

AutoGPT

✓✓✓

✓✓

✓✓

✓✓

✓✓✓

✓

✓✓✓

ChatGPT

✓✓✓

✓✓

✓

✓✓

✓✓✓

✓

✓✓

✓

✓✓

✓

✓✓

✓✓✓

✓

✓✓✓

Open source LLMs∗

Adv. Sci. 2024, 11, 2407094

2407094 (4 of 15)

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 5

www.advancedscience.com

Table 2. Summary of AutoBA application scenarios in bioinformatics multi-omics analysis. The table displays a comprehensive list of 40 real-world cases
utilized to assess AutoBA, providing information on the class of the cases, the respective task name, and the corresponding case ID.
Bioinformatics Pipelines

Tasks

Types of Omics

Case ID

WGS data analysis

Genome assembly

Genomics

1.1

WGS/WES data analysis

Somatic SNV+indel calling

Genomics

2.1

WGS/WES data analysis

Somatic SNV+indel calling and annotation

Genomics

2.2

WGS/WES data analysis

Structure variation identiﬁcation with normal

Genomics

2.3

WGS/WES data analysis

Structure variation identiﬁcation without normal

Genomics

2.4

ChIP-seq data analysis

Peak calling

Genomics

3.1

ChIP-seq data analysis

Motif discovery for binding sites

Genomics

3.2

ChIP-seq data analysis

Functional enrichment of target gene

Genomics

3.3

Bisulﬁte-Seq data analysis

Identifying DNA methylation

Genomics

4.1

ATAC-seq data analysis

Identifying open chromatin regions

Genomics

5.1

DNase-seq data analysis

Identifying Dnasel hypersensitive site

Genomics

6.1

4C-seq data analysis

Find genomics interactions

Genomics

7.1

Nanopore DNA sequencing data analysis

Genome assembly

Genomics

8.1

Nanopore DNA sequencing data analysis

Tandem repeats variation identiﬁcation

Genomics

8.2

PacBio DNA sequencing data analysis

Genome assembly

Genomics

9.1

RNA-Seq data analysis

Find Diﬀerentially expressed genes

Transcriptomics

10.1

RNA-Seq data analysis

Identify the top5 downregulated genes

Transcriptomics

10.2

RNA-Seq data analysis

Predict Fusion gene with annotation

Transcriptomics

10.3

RNA-Seq data analysis

Isoform expression

Transcriptomics

10.4

RNA-Seq data analysis

Splicing analysis

Transcriptomics

10.5

RNA-Seq data analysis

APA analysis

Transcriptomics

10.6

RNA-Seq data analysis

RNA editing

Transcriptomics

10.7

RNA-Seq data analysis

Circular RNA identiﬁcation

Transcriptomics

10.8

Small RNA sequencing data analysis

microRNA quantiﬁcation

Transcriptomics

11.1

Small RNA sequencing data analysis

microRNA prediction

Transcriptomics

11.2

CAGE-seq data analysis

TSS identiﬁcation

Transcriptomics

12.1

3’ end-seq data analysis

PAS (polyadenylation site) identiﬁcation

Transcriptomics

13.1

Nanopore RNA sequencing data analysis

Isoform expression

Transcriptomics

14.1

PacBio RNA sequencing data analysis

Isoform expression

Transcriptomics

15.1

CLIP-seq data analysis

Identify protein-RNA crosslink sites

Transcriptomics

16.1

RIP-seq data analysis

Find enriched genes bounded by RBP

Transcriptomics

16.2

Ribo-seq data analysis

Identify translated ORFs

Transcriptomics

17.1

single-cell RNA-seq data analysis

Cell clustering from fastq data

Transcriptomics

18.1

single-cell RNA-seq data analysis

Find diﬀerentially expressed genes based on count matrix

Transcriptomics

18.2

single-cell RNA-seq data analysis

Find marker genes based on count matrix

Transcriptomics

18.3

single-cell RNA-seq data analysis

Cell clustering and visualization

Transcriptomics

18.4

Spatial transcriptomics

Neighborhood enrichment analysis

Transcriptomics

19.1

Spatial transcriptomics

Single-cell mapping

Transcriptomics

19.2

Mass spectrometry data analysis

Protein expression quantiﬁcation

Proteomics

20.1

Mass spectrometry data analysis

Metabolites quantiﬁcation

Metabolomics

21.1

meticulously logs the outcome of each step in a speciﬁc format,
and all these historical records become part of the input for
the subsequent prompt. In the planning phase, memories are
structured as follows: “First, you provided input in the format
‘ﬁle path: ﬁle description’ in a list: <data list>. You devised a
detailed plan to accomplish your overarching objective. Your
overarching goal is <global goal>. Your plan involves <tasks>.”
In the code generation phase, memories follow this format:
“Then, you successfully completed the task: <task> with the
corresponding code: <code>.”

Adv. Sci. 2024, 11, 2407094

2407094 (5 of 15)

2.4. Automatic Code Repair of AutoBA
AutoBA incorporates an automatic code repair (ACR) module
designed to streamline the debugging process and enhance
the reliability of generated code. During the code execution
phase, AutoBA identiﬁes errors from the output stream called
standard error (stderr) and standard output (stdout). Once an
error is detected, these detected errors will be integrated into the
prompt for code regeneration, ensuring a repetitive cycle until
the generated code successfully executes without errors.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 6

www.advancedscience.com

2.5. Evaluation of AutoBA
The results produced by AutoBA undergo thorough validation by
bioinformatics experts. This validation process encompasses a
comprehensive review of the proposed plans, generated codes,
execution of the code, and conﬁrmation of the results for accuracy and reliability. AutoBA’s development and validation are
built upon a speciﬁc environment and software stack, which includes Ubuntu version 20.04, Python 3.10.0, and openai version
0.27.6. These environment and software speciﬁcations form the
robust foundation for AutoBA’s functionality in the ﬁeld of bioinformatics, ensuring its reliability and eﬀectiveness. To further assess the usability of AutoBA, a comparative analysis involving the
following methods was conducted: 1) AutoBA (w/o ACR, online
with ChatGPT-4), 2) AutoBA (with ACR, online with ChatGPT4), 3) AutoBA (w/o ACR, oﬄine with CodeLlama-34B-Instruct),
4) AutoBA (with ACR, oﬄine with CodeLlama-34B-Instruct), 5)
AutoGPT, 6) ChatGPT-3.5, 7) ChatGPT-4 and 8) CodeLlama-34BInstruct. Given that prompt engineering and workﬂow design is
a distinctive innovation of AutoBA, during the evaluation of AutoGPT, ChatGPT-3.5, ChatGPT-4, and CodeLlama-34B-Instruct,
user behavior was emulated by utilizing a generalized and uniform prompt as shown in the supplementary information.

2.6. Online and Local LLM Backends of AutoBA
AutoBA oﬀers several versions of LLM backends, including online backends based on ChatGPT-3.5 and ChatGPT-4, and local LLMs, including CodeLlama-7B-Instruct, CodeLlama-13BInstruct, CodeLlama-34B-Instruct,[67] Llama-2-7b-chat, Llama-213b-chat and Llama-2-70b-chat.[68]

the oﬄine version requires GPU support (7B: 12.55GB, 13B:
24GB, 34B: 63GB, 70B: 74GB). The sizes mentioned, such as
7B, 13B, 34B, and 70B, indicate the number of parameters in the
models (B stands for billion). The corresponding GPU memory
requirements in gigabytes (GB) are listed next to each model size.
2.8. Statistical Analysis
During the evaluation of AutoBA, all experimental data were examined at least three times on the same computational environment and data. Statistical analysis was performed using Python
packages.

3. Results
3.1. AutoBA Proposes Detailed Analysis Plans for Tasks
AutoBA oﬀers a robust capability to generate a highly detailed
and customized analysis plan, leveraging the user’s input, which
encompasses critical elements such as data paths, data descriptions, and objective descriptions.
As an example, in Figure 3, the user supplied four RNA-Seq
samples: two from the LoGlu group (SRR1374921.fastq.gz
and SRR1374922.fastq.gz, mouse pancreatic islets cultured
at low ambient glucose) and two from the HiGlu group
(SRR1374923.fastq.gz and SRR1374924.fastq.gz, mouse pancreatic islets cultured at high ambient glucose) from Benner et al.’s paper.[69] Additionally, the user also provided the
mouse reference genome (mm39.fa) and genome annotation
(mm39.ncbiRefSeq.gtf). The primary objective of this case was
to identify diﬀerentially expressed genes between the two data
groups. Using textual inputs only, AutoBA generated a detailed,
step-by-step analysis plan during the planning phase, as outlined
below:

2.7. Security and Safety of AutoBA
AutoBA incorporates a sandbox mode to establish a secure
and isolated environment for conducting analyses. This mode
encapsulates the analysis processes, eﬀectively shielding the
underlying system from potential threats. Meanwhile, AutoBA
imposes restrictions on system commands throughout the
execution phase, thereby reducing the risk of malicious commands being executed within the environment. Additionally,
AutoBA leverages Docker containerization, introducing an extra
layer of security to further fortify the overall system integrity.
Furthermore, Docker containerization simpliﬁes the installation process, contributing to a reduction in learning costs for
users. A workstation with 252 GB RAM, 112 CPU cores, and 1
Nvidia A100 GPU was adopted for all experiments. AutoBA was
developed based on Python3.10 and CUDA12.0. CUDA is a parallel computing platform and programming model developed by
NVIDIA. AutoBA utilizes LLMs as its core for generating analysis
plans and code. These models beneﬁt greatly from GPU acceleration. CUDA allows for faster computation of model parameters,
leading to quicker generation of results and more eﬃcient handling of complex natural language processing tasks. A detailed
list of dependencies could be found in the code availability.
The online version operates without the need for a GPU, while

Adv. Sci. 2024, 11, 2407094

2407094 (6 of 15)

1) First, I will use the “Trimmomatic” software to trim
the adapters from the single-end mouse rna-seq
reads. The input ﬁles for this step will be “./data/
SRR1374921.fastq.gz”, “./data/SRR1374922.fastq.gz”,
“./data/SRR1374923.fastq.gz”,
“./data/SRR1374924.fastq.gz” and the adapter ﬁle
“./data/TruSeq3-SE.fa”.
2) Next, I will use the “Hisat2” software to align the trimmed
reads to the mouse mm39 genome. The input ﬁles for this
step will be the output ﬁles from the previous step and the
genome ﬁle “./data/mm39.fa”.
3) Then, I will use the “Samtools” software to convert the
alignment output ﬁles from Hisat2 (in SAM format) to BAM
format.
4) After that, I will use the “HTSeq” software to count the number of reads mapped to each gene. The input ﬁles for this
step will be the BAM ﬁles from the previous step and the
annotation ﬁle “./data/mm39.ncbiRefSeq.gtf”.
5) Finally, I will use the “DESeq2” software to identify the differentially expressed genes. The input ﬁles for this step will
be the count ﬁles from the previous step.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 7

www.advancedscience.com

Figure 3. Example of applying AutoBA to ﬁnd diﬀerentially expressed genes with RNA-Seq data. In this case, the user provided four RNA-seq samples,
comprising two from the LoGlu group and two from the HiGlu group. The primary objective of this analysis was to identify diﬀerentially expressed genes
between two groups. During the automated analysis prior to the alignment run by AutoBA, the ACR module identiﬁed an error where Hisat2 did not ﬁrst
index the genome. Consequently, the ACR module automatically corrected the code (highlighted in blue). This case demonstrates that AutoBA can be
used for end-to-end bioinformatics analysis. Users only need to provide the simplest inputs, and AutoBA will deliver the ﬁnal analysis results.

Adv. Sci. 2024, 11, 2407094

2407094 (7 of 15)

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 8

www.advancedscience.com

Within each step of the plan outlined above, AutoBA provides
precise instructions regarding the required software, including
names like Trimmomatic, Hisat2, Samtools, HTSeq, and DESeq2, along with clear sub-tasks for each analytical stage. This
level of tailored planning ensures that the analysis process aligns
precisely with the user’s objectives, promoting both eﬃciency
and accuracy in data processing and results generation.
3.2. AutoBA Generates Precise Codes for Sub-Tasks
During the code generation phase, AutoBA generates code in
bash format for every sub-task of the plan established in the
planning phase. These scripts encompass environment setup,
software installation, and tailored code for software utilization.
Parameters and data paths speciﬁc to the software are meticulously incorporated. As exempliﬁed in Figure 3, the preliminary
phase of the diﬀerentially expressed genes (DEG) analysis constitutes the essential process of adapter trimming, an indispensable
preprocessing step in the context of raw RNA-Seq data. Within
this critical step, AutoBA automatically generated code, including
activating the conda environment, installing software packages,
and calling software to analyze data as shown below:

source activate abc_runtime
conda conﬁg –add channels conda-forge
conda conﬁg –add channels bioconda
conda install -y trimmomatic
trimmomatic SE -phred33 ./data/SRR1374921.fastq.gz
./output/SRR1374921_trimmed.fastq.gz
ILLUMINACLIP:./data/TruSeq3-SE.fa:2:30:10
trimmomatic SE -phred33 ./data/SRR1374922.fastq.gz
./output/SRR1374922_trimmed.fastq.gz
ILLUMINACLIP:./data/TruSeq3-SE.fa:2:30:10
trimmomatic SE -phred33 ./data/SRR1374923.fastq.gz
./output/SRR1374923_trimmed.fastq.gz
ILLUMINACLIP:./data/TruSeq3-SE.fa:2:30:10
trimmomatic SE -phred33 ./data/SRR1374924.fastq.gz
./output/SRR1374924_trimmed.fastq.gz
ILLUMINACLIP:./data/TruSeq3-SE.fa:2:30:10

The generated code further underwent a meticulous and thorough validation process, which included a manual veriﬁcation
and execution performed by experienced and proﬁcient bioinformaticians, as meticulously documented in Table 3 and Supplementary information. This critical validation step ensures the accuracy and reliability of the code, reaﬃrming the robustness of
AutoBA.
3.3. AutoBA Adeptly Manages Similar Tasks with Robustness
In practical bioinformatics applications, even when researchers
are working with similar data types, such as RNA-Seq, it is noteworthy that analyses often manifest variations stemming from
diverse sources. These variations are primarily attributed to disparities in the characteristics of input data and the distinct objectives pursued in the analytical process.

Adv. Sci. 2024, 11, 2407094

2407094 (8 of 15)

As exempliﬁed in Case 10.1 (ﬁnd diﬀerentially expressed
genes), Case 10.2 (identify the top ﬁve down-regulated genes in
HiGlu group), and Case 10.3 (predict fusion genes), when performing RNA-Seq analysis, users may have distinct ﬁnal goals,
necessitating adjustments in software and parameter selection
during the actual execution. In comparison to case 10.1, AutoBA
introduces an additional step in case 10.2, tailored for screening
the top ﬁve diﬀerentially expressed genes to fulﬁll the user’s speciﬁc requirements as shown in the code below:
Rscript -e ‘‘library(’pheatmap’); library(’DESeq2’);
res <- read.csv(’./examples/output/diﬀerential_expression_
results.csv’, row.names = 1); res_ordered <res[order(res$log2FoldChange),]; top5_downregulated <head(res_ordered, 5);

3.4. AutoBA Adjusts Analysis Based on Task and Input Data
Variations
Alignment is an essential step for bioinformatic analysis, for
which multiple tools have been developed for distinct tasks. For
instance, tools including STAR[70] and HISAT2[71] designed for
RNA-seq data analysis are splicing aware, which is eﬃcient in
identifying junction reads that map to two distal positions in
the reference genome. Besides, long-read sequencing data from
Paciﬁc Bioscience (PacBio) and Oxford Nanopore Technology
(ONT) also require specialized tools for the alignment, for which
Minimap2[72] is the most widely used method. Moreover, each
read from single-cell sequencing data contains barcodes for UMI
and cell labels, which needs to be integrated with the alignment.
CellRanger is a popular software with this capacity. Therefore,
bioinformatic analysis should use appropriate tools for the alignment based on the types of tasks. Interestingly, we found that
AutoBA has learned this knowledge and can correctly employ the
tool for the alignment (Figure 4a).
For many bioinformatic analyses, multiple tools are available
but require diﬀerent conditions of inputs. For instance, to identify structural variations from tumor WGS/WES data, the method
“manta”[73] can handle the analysis against the matched normal.
On the other hand, tools like “Pindel”[74] that relies on the detection of breakpoints with the reference genome, only conduct
analysis on the tumor samples. We found that AutoBA can automatically select “manta” when the matched normal samples were
provided and correctly utilized the parameters “–normalBam”
and “–tumorBam”. However, if only the tumor samples were provided in the input data, AutoBA will select “Pindel” for the analysis (Figure 4b). These results suggest that AutoBA learned the
requirements of diﬀerent bioinformatic tools and is capable of
selecting appropriate tools based on diﬀerent conditions of the
input data.
manta –normalBam ./output/SRR23015874.recalibrated.bam
–tumorBam ./output/SRR23015876.recalibrated.bam
–referenceFasta ./data/hg38.fa –runDir ./output/manta_SRR23015874

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 9

www.advancedscience.com

Table 3. Summary of AutoBA (w/o ACR) generated results evaluated by bioinformatics experts. The table presents an assessment conducted by bioinformatics experts on the analysis plan proposed by AutoBA, along with the generated codes and the code execution. If the evaluation passes, it is displayed
as success, while instances of failure are accompanied by detailed explanations of the speciﬁc reasons for the failure. Additionally, we provide a summary
of the software tools automatically chosen by AutoBA for each case, as well as the total time taken to generate the corresponding code.
Case ID

Propose Plans

Generate Codes

Execute Codes

Tools Used

Time Cost (without
Executing Codes) in
Minutes

1.1

Success

Success

Success

FastQC, Trimmomatic[ 76] , SPAdes[ 77] , QUAST[ 78]

3

2.1

Success

Success

Success

FastQC, Trimmomatic, BWA[ 79] , Samtools[ 80] , GATK[81]

8

2.2

Success

Success

Success

FastQC, Trimmomatic, BWA, Samtools, GATK,
ensembl-vep[ 82]

8

2.3

Success

Success

Success

FastQC, Trimmomatic, BWA, Samtools, GATK, manta[ 73]

18

2.4

Success

Success

Failed: pindel requires
conﬁguration ﬁle

FastQC, Trimmomatic, BWA, Samtools, pindel[ 74] ,
SnpEﬀ[83]

6

3.1

Success

Success

Success

FastQC, Trim Galore, Bowtie 2[ 84] , Samtools, MACS2[ 85] ,
BEDTools, IGV

6

3.2

Success

Success

Success

FastQC, Trim Galore, Bowtie2, MACS2, HOMER,
MEME[86]

4

3.3

Failed: DESeq2 is
not suitable for
peaks identiﬁed
by MACS2

–

–

FastQC, BWA, MACS, BEDTools[87] , DESeq2[ 88] ,
g:Proﬁler[ 89] , R[90]

6

4.1

Success

Success

Success

Trim Galore, Bismark[ 91] , IGV[92]

9

5.1

Success

Success

Failed: (wrongly used
BEDTools)

Trim Galore, BWA, Samtools, MACS2, BEDTools

8

6.1

Success

Success

Success

FastQC, Cutadapt, BWA, MACS2, IGV, GREAT[93]

5

7.1

Success

Success

Success

FastQC, BEDTools, Samtools, Bowtie 2, R

6

8.1

Success

Success

Failed: racon medaka
wrongly used the
parameters

canu[ 94] , Minimap2[ 72] , Racon[95] , Flye[ 96] , Medaka,
Bandage[97]

7

8.2

Failed: cannot
ﬁnd a correct
pipeline

–

–

Minimap2, Samtools, trf[98]

7

9.1

Success

Failed: install the
wrong tool,
pb-falcon rather
than falcon

–

Canu, FALCON[ 99] , Quiver, MUMmer[ 100]

7

5

10.1

Success

Success

Success

FASTQC, Trimmomatic, HISAT2[ 71] , htseq[ 101] , DESeq2

10.2

Success

Success

Success

FASTQC, Trimmomatic, HISAT2, htseq, DESeq2, gproﬁleR

5

10.3

Success

Success

Success

gunzip, HISAT2, fusioncatcher[ 102] , gﬀcompare[ 103]

6

10.4

Success

Success

Success

Trim Galore, HISAT2, Samtools, StringTie

5

10.5

Success

Success

Success

Trimmomatic, HISAT2, Samtools, StringTie,
featureCounts[ 36] , rMATs[38]

6

10.6

Success

Failed: DaPars (not
available in conda)

–

Trim Galore, HISAT2, StringTie, DaPars[104]

7

10.7

Failed: cannot
ﬁnd a correct
pipeline

–

–

FastQC, Trimmomatic, HISAT2, Samtools, StringTie,
ballgowan[ 105] , GATK

7

10.8

Success

Failed: CIRI2 (not
available in conda)

–

Trim Galore, HISAT2, CIRI2[ 106] , CIRIQuant[ 107]

5

11.1

Success

Success

Success

Fastqc, Cutadapt, Bowtie, Samtools,
subread/featureCounts, DESeq2, edgeR[ 108]

11

11.2

Success

Success

Failed: conda of
miRDeep2 is
problematic

Fastqc, Cutadapt, Bowtie, Samtools, featureCounts,
miRDeep2, DESeq2, edgeR

11

(Continued)

Adv. Sci. 2024, 11, 2407094

2407094 (9 of 15)

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 10

www.advancedscience.com

Table 3. (Continued)
Case ID

Propose Plans

Generate Codes

Execute Codes

Tools Used

Time Cost (without
Executing Codes) in
Minutes

12.1

Success

Success

Success

Fastqc, Trimmomatic, HISAT2, HTSeq/htseq-count,
CAGEr[109]

6

13.1

Failed: cannot
ﬁnd a correct
pipeline

–

–

Trim Galore, HISAT2, StringTie, DaPars

5

14.1

Success

Success

Failed: prepDE.py no
need to run with
’python prepDE.py’

Minimap2, Samtools, StringTie, DESeq2

9

15.1

Success

Success

Success

Minimap2, Samtools, StringTie, cuﬄinks[ 110]

5

16.1

Success

Success

Failed: conda of
Piranha is
problematic

FastQC, Cutadapt, Bowtie2, Samtools, BEDTools, Piranha

6

16.2

Success

Success

Success

FastQC, Trim Galore, HISAT2, htseq, DESeq2

4

17.1

Success

Success

Failed: not regular
conda of ribotaper

FastQC, Trim Galore, HISAT2, Samtools, StringTie,
RiboTaper[111]

7

18.1

Success

Success

Success

Cell Ranger, Seurat[ 112]

5

18.2

Success

Success

Success

Scanpy[113]

8

18.3

Success

Success

Success

Scanpy

6

18.4

Success

Success

Success

Scanpy

5

19.1

Success

Success

Success

Squidpy[114] , AnnData

5

19.2

Success

Success

Success

AnnData, Scanpy, Tangram[115]

3

20.1

Success

Success

Success

proteowizard[ 116] , OpenMS[ 117]

15

21.1

Success

Success

Success

pymzml[ 118] , pandas, numpy, scipy

13

#Success

36

33

26

–

–

3.5. Apply AutoBA to a Variety of Conventional Multi-Omic
Analysis Scenarios

3.6. AutoBA Reduces Human Intervention and Increases
Robustness Compared to Other Methods

To evaluate the robustness of AutoBA, we conducted assessments
involving a total of 40 cases spanning four distinct types of omics
data: genomics, transcriptomics, proteomics, and metabolomics
as shown in Table 2 and Supporting Information.
All cases underwent an independent analysis process conducted by AutoBA and were subsequently subjected to validation
by experienced bioinformatics experts. The collective results underscore the versatility and robustness of AutoBA across a spectrum of multi-omics analysis procedures in the ﬁeld of bioinformatics as shown in Table 3. AutoBA demonstrates its capability
to autonomously devise novel analysis processes based on varying input data, showcasing its adaptability to diverse input data
and analysis objectives with a success rate of 90% (36 out of 40)
for proposing plans, 82.5% (33 out of 40) for generating codes
to obtain and install appropriate tools, and 65% (26 out of 40)
for automated end-to-end analysis. With the incorporation of the
ACR module, AutoBA demonstrates enhanced robustness, with
the same success rate of 90% (36 out of 40) for proposing plans,
but a higher success rate of 87.5% (35 out of 40) for generating
codes to obtain and install appropriate tools, and 87.5% (35 out
of 40) for automated end-to-end analysis. Compared to the online
version, the local version showed a slight decline in performance
as shown in Figure 4d.

As shown in Figure 4c, we conducted a conceptual comparison
between AutoBA and alternative methods in terms of human
intervention. In utilizing conventional bioinformatics tools and
web servers, users are required to prepare input data and comprehend detailed analysis plans prior to execution. Throughout
the execution phase, users must conﬁgure the environment,
install essential dependencies, write code, and proceed with
step-by-step debugging. In contrast, ChatGPT and other opensource LLMs assist users in proposing step-by-step plans and
generating code, thus mitigating human intervention. Nevertheless, users still need to manually conﬁgure the environment,
execute code, and perform debugging. AutoGPT, functioning as
an AI agent, aids users in executing generated code to further
minimize human intervention. However, within the context of
bioinformatics data analysis, AutoGPT encounters challenges in
setting up the environment and debugging for users. Conversely,
AutoBA signiﬁcantly reduces human intervention, necessitating
only the preparation of input data.
To show the robustness of AutoBA, we further conducted
a comprehensive comparison of eight methods, including 1)
AutoBA (w/o ACR, online with ChatGPT-4), 2) AutoBA (with
ACR, online with ChatGPT-4), 3) AutoBA (w/o ACR, oﬄine
with CodeLlama-34B-Instruct), 4) AutoBA (with ACR, oﬄine

Adv. Sci. 2024, 11, 2407094

2407094 (10 of 15)

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 11

www.advancedscience.com

Figure 4. Results of AutoBA and the comparison with other methods. a) Heatmap illustrating options of utilizing diﬀerent alignment tools for multiple
tasks planned by AutoBA. b) AutoBA utilizes the tools for identifying structure variations in tumor samples with or without the matched normal samples.
The highlight shows the diﬀerence between Goal 1 and Goal 2. c) Conceptual comparison of AutoBA with other methods in terms of human intervention.
Orange indicates the need for human intervention, while green signiﬁes an absence of human intervention (fully automated process). d) Evaluation of
results generated by various methods by manually checking and executing codes and comparing them to standard analysis pipelines. Orange indicates
a failure, and blue indicates a success.

Adv. Sci. 2024, 11, 2407094

2407094 (11 of 15)

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 12

www.advancedscience.com

with CodeLlama-34B-Instruct), 5) AutoGPT, 6) ChatGPT-3.5, 7)
ChatGPT-4 and 8) CodeLlama-34B-Instruct, across all 40 cases,
as illustrated in Figure 4d. AutoBA showed better performance in
comparison to AutoGPT (90% for proposing plans, 25% for generating codes to obtain and install appropriate tools, and 0% for
automated end-to-end analysis), ChatGPT-3.5 (92.5% for proposing plans, 30% for generating codes to obtain and install appropriate tools, and 2.5% for automated end-to-end analysis),
ChatGPT-4 (92.5% for proposing plans, 37.5% for generating
codes to obtain and install appropriate tools, and 7.5% for automated end-to-end analysis), and CodeLlama-34B-Instruct (80%
for proposing plans, 7.5% for generating codes to obtain and install appropriate tools, and 2.5% for automated end-to-end analysis).

4. Discussion
To our knowledge, AutoBA is the ﬁrst autonomous AI agent tailored explicitly for conventional multi-omic analyses for omics
data. AutoBA streamlines the analytical process, requiring minimal user input while providing detailed step-by-step plans for
various bioinformatics tasks (Video S1, Supporting Information).
The results of our investigation reveal that AutoBA excels in accurately handling a diverse array of omics analysis tasks, such
as RNA-seq, scRNA-seq, ChIP-seq, spatial transcriptomics, and
so on. One of the key strengths of AutoBA is its adaptability to
variations in analysis objectives. As demonstrated in the cases
presented, even with similar data types, such as RNA-Seq, users
often have distinct goals, necessitating modiﬁcations in software
and parameter selection during execution. AutoBA eﬀectively accommodates these variations, allowing users to tailor their analyses to speciﬁc research needs without compromising accuracy.
Furthermore, AutoBA’s versatility is highlighted by its ability to
self-design new analysis processes based on diﬀering input data.
This autonomous adaptability makes AutoBA a valuable tool for
bioinformaticians working on novel or unconventional research
questions, as it can adjust its approach to the unique characteristics of the data.
Online bioinformatics analysis platforms are currently in
vogue, but they often necessitate the uploading of either raw data
or pre-processed statistics by users, which could potentially give
rise to privacy concerns and data leakage risks. In contrast, AutoBA addresses these privacy issues by oﬀering both online version and local version. When utilizing the online version of AutoBA with ChatGPT, data uploads are unnecessary, requiring only
descriptive information in natural language as speciﬁed in our
prompt design. This information is limited in terms of private
details. In comparison, the local version of AutoBA provides the
highest level of privacy protection, as it operates on local backends and eliminates the need to share any information with third
parties. Moreover, AutoBA showcases its adaptability in sync with
emerging bioinformatics tools, with LLM seamlessly incorporating these latest tools into the database. Furthermore, AutoBA is
inclined toward selecting the most popular analytical frameworks
or widely applicable tools in the planning phase, underscoring its
robustness. Another distinguishing feature is AutoBA’s transparent and interpretable execution process. This transparency allows
professional bioinformaticians to easily modify and customize

Adv. Sci. 2024, 11, 2407094

2407094 (12 of 15)

AutoBA’s outputs, leveraging AutoBA to expedite the data analysis process.
AutoBA is also a future-proof AI agent designed for bioinformatics analysis, leveraging LLMs as its core. This design allows AutoBA to integrate with any existing LLM, whether online
(e.g., ChatGPT, GPT-4, GPT-4o) or oﬄine (e.g., LLaMA, CodeLLaMA, and DeepSeek). The LLM used in AutoBA is fully substitutable, enabling it to beneﬁt from the continual advancements
in LLM technology. As new state-of-the-art LLMs are developed,
AutoBA can incorporate them to enhance its performance in automatic bioinformatics analysis. Still, AutoBA’s limitation in tool
selection does exist. Current LLMs are trained on internet data,
meaning that widely used methods in bioinformatics are typically well-trained, while methods from speciﬁc papers may be
underrepresented or not trained at all. As a result, the best outcomes are achieved when using tools that have been extensively
trained, which can lead to potential biases in tool selection. To
address this, training a specialized LLM for bioinformatics that
thoroughly covers all tools and methods in the ﬁeld could be a
solution in the future.
Given that classical bioinformatic analysis encompasses a far
broader spectrum of tasks and challenges than the 40 cases studied in this work (Tables 2 and 3), it is essential to conduct more
real-world applications by our potential users to further comprehensively validate the robustness of AutoBA. We found that
a large proportion (36%, 5 out of 14) of failed cases in executing code is due to the tools in conda being problematic, not in
a regular form (end with .sh, .pl et al), or requiring an edited
conﬁg ﬁle, suggesting a demand for more standard bioinformatics tools. Furthermore, taking into account the timeliness of the
training data used for large language models, it’s important to
note that some of the most recently proposed methods in bioinformatics may still pose challenges in automatically generating
code by AutoBA. Therefore, a future endeavor to train an up-todate large language model explicitly tailored for bioinformatics
can signiﬁcantly enhance AutoBA’s ability to maintain up-to-date
code generation capabilities. Nevertheless, AutoBA represents a
signiﬁcant advancement in the ﬁeld of bioinformatics, oﬀering
a user-friendly, eﬃcient, and adaptable solution for a wide range
of omics analysis tasks. Its capacity to handle diverse data types
and analysis goals, coupled with its robustness and adaptability, positions AutoBA as a valuable asset in the pursuit of accelerating bioinformatics research. We anticipate that AutoBA will
ﬁnd extensive utility in the scientiﬁc community, supporting researchers in their quest to extract meaningful insights from complex biological data.

Supporting Information
Supporting Information is available from the Wiley Online Library or from
the author.

Acknowledgements
J.Z., B.Z., X.C., H.L., X.X., S.C., W.H., C.X., and X.G. were supported in part
by grants from the Oﬃce of Research Administration (ORA) at King Abdullah University of Science and Technology (KAUST) under award number
FCC/1/1976-44-01, FCC/1/1976-45-01, REI/1/5202-01-01, REI/1/5234-0101, REI/1/4940-01-01, RGC/3/4816-01-01, REI/1/0018-01-01, REI/1/541401-01, REI/1/5289-01-01, and REI/1/5404-01-01.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 13

www.advancedscience.com

Conﬂict of Interest
The authors declare no conﬂict of interest.

Author Contributions
J.Z. and B.Z. contributed equally to this work. J.Z. and X.G performed conceptualization. J.Z., B.Z., and X.G. performed design. J.Z. performed code
Implementation. J.Z., B.Z., X.C., H.L., C.X., and W.H. performed application. J.Z. and B.Z. wrote the original draft of the manuscript. J.Z., B.Z., X.X.,
S.C., X.G., L.L., and G.L. performed critical revision of the manuscript for
important intellectual content. J.Z. and X.G. performed supervision. X.G.
performed funding acquisition.

Code Availability Statement
The AutoBA software is publicly available at https://github.com/
JoshuaChou2018/AutoBA. The Docker version of AutoBA is available at
https://hub.docker.com/r/joshuachou666/autoba.

Data Availability Statement
The RNA-seq dataset could be downloaded from Sequence Read
Archive (SRA) with IDs: SRR1374921, SRR1374922, SRR1374923, and
SRR1374924. The dataset for case 1.3 could be downloaded from https:
//github.com/STAR-Fusion/STAR-Fusion-Tutorial/wiki. The scRNA-seq
dataset could be downloaded from http://cf.10xgenomics.com/samples/
cell-exp/1.1.0/pbmc3k/pbmc3k_ﬁltered_gene_bc_matrices.tar.gz.
The
ChIP-seq dataset could be downloaded with IDs: SRR620204, SRR620205,
SRR620206, and SRR620208. The Spatial Transcriptomics dataset could be
downloaded from https://doi.org/10.5281/zenodo.6334774. The CAGEseq dataset could be downloaded from SRA with IDs: SRR11351697,
SRR11351698, SRR11351700, and SRR11351701. The 3’end-seq dataset
could be downloaded from SRA with IDs: SRR17422754, SRR17422755,
SRR17422756, and SRR17422757. The CLIP-seq dataset could be
downloaded from ENCODE (https://www.encodeproject.org) with
IDs: ENCLB742AYH and ENCLB770EDJ. The Ribo-seq data could be
downloaded from SRA with IDs: RR12354645 and RR12354646. The
raw single-cell RNA sequencing data could be downloaded from 10X
genomics. The PacBio long-read sequencing data could be downloaded
from SRA with IDs: SRR19552218 and SRR19785215. The small RNA-seq
data could be downloaded from the previous study.[75]

Keywords
agent, bioinformatics, large language model, omics analysis
Received: June 25, 2024
Revised: August 11, 2024
Published online: October 3, 2024

[1] N. M. Luscombe, D. Greenbaum, M. Gerstein, Methods of information in medicine 2001, 40, 346.
[2] J. Gauthier, A. T. Vincent, S. J. Charette, N. Derome, Brieﬁngs in bioinformatics 2019, 20, 1981.
[3] A. D. Baxevanis, G. D. Bader, D. S. Wishart, Bioinformatics, John Wiley & Sons, NJ, USA 2020.
[4] P. Munk, C. Brinch, F. D. Møller, T. N. Petersen, R. S. Hendriksen,
A. M. Seyfarth, J. S. Kjeldgaard, C. A. Svendsen, B. van Bunnik, F.
Berglund, Nat. Commun. 2022, 13, 7251.

Adv. Sci. 2024, 11, 2407094

2407094 (13 of 15)

[5] E. H. Lips, T. Kumar, A. Megalios, L. L. Visser, M. Sheinman, A.
Fortunato, V. Shah, M. Hoogstraat, E. Sei, D. Mallo, Nat. Genet.
2022, 54, 850.
[6] D. T. Jones, J. M. Thornton, Nat. Methods 2022, 19, 15.
[7] M. L. Hekkelman, I. de Vries, R. P. Joosten, A. Perrakis, Nat. Methods
2023, 20, 205.
[8] N. Sapoval, A. Aghazadeh, M. G. Nute, D. A. Antunes, A. Balaji,
R. Baraniuk, C. Barberan, R. Dannenfelser, C. Dun, M. Edrisi, Nat.
Commun. 2022, 13, 1728.
[9] T. Gupta, M. Zaki, N. A. Krishnan, Mausam, npj Comput. Mater.
2022, 8, 102.
[10] Z. Zeng, Y. Yao, Z. Liu, M. Sun, Nat. Commun. 2022, 13, 862.
[11] N. De Maio, P. Kalaghatgi, Y. Turakhia, R. Corbett-Detig, B. Q. Minh,
N. Goldman, Nat. Genet. 2023, 55, 746.
[12] A. S. Chanderbali, L. Jin, Q. Xu, Y. Zhang, J. Zhang, S. Jian, E. Carroll,
D. Sankoﬀ, V. A. Albert, D. G. Howarth, Nat. Commun. 2022, 13, 643.
[13] J. Rhodes, A. Abdolrasouli, K. Dunne, T. R. Sewell, Y. Zhang, E.
Ballard, A. P. Brackin, N. van Rhijn, H. Chown, A. Tsitsopoulou, Nat.
Microbiol. 2022, 7, 663.
[14] A. Heinken, J. Hertel, G. Acharya, D. A. Ravcheev, M. Nyga, O.
E. Okpala, M. Hogan, S. Magnúsdóttir, F. Martinelli, B. Nap, Nat.
Biotechnol. 2023, 41, 1320.
[15] F. Hemmerling, J. Piel, Nat. Rev. Drug Discovery 2022, 21, 359.
[16] J. Zhou, B. Zhang, H. Li, L. Zhou, Z. Li, Y. Long, W. Han, M. Wang,
H. Cui, J. Li, Genomics, Proteomics and Bioinformatics 2022, 20, 959.
[17] H. Li, H. Li, J. Zhou, X. Gao, Bioinformatics 2022, 38, 4878.
[18] T. Zhang, L. Li, H. Sun, D. Xu, G. Wang, Brieﬁngs in Bioinformatics
2023, 24, bbad316.
[19] Z. Li, E. Gao, J. Zhou, W. Han, X. Xu, X. Gao, Cell Reports Methods
2023, 3.
[20] Y. Long, B. Zhang, S. Tian, J. J. Chan, J. Zhou, Z. Li, Y. Li, Z. An, X.
Liao, Y. Wang, Genome Res. 2023, 33, 644.
[21] A. F. Bardet, Q. He, J. Zeitlinger, A. Stark, Nat. Protoc. 2012, 7, 45.
[22] B. Vieth, S. Parekh, C. Ziegenhain, W. Enard, I. Hellmann, Nat. Commun. 2019, 10, 4667.
[23] M. D. Luecken, F. J. Theis, Molecular systems biology 2019, 15, e8746.
[24] F. C. Grandi, H. Modi, L. Kampman, M. R. Corces, Nat. Protoc. 2022,
17, 1518.
[25] P. C. Ng, E. F. Kirkness, Genetic variation: Methods and protocols 2010,
628, 215.
[26] Z. Wang, M. Gerstein, M. Snyder, Nat. Rev. Genet. 2009, 10, 57.
[27] A.-E. Saliba, A. J. Westermann, S. A. Gorski, J. Vogel, Nucleic Acids
Res. 2014, 42, 8845.
[28] J. D. Buenrostro, B. Wu, H. Y. Chang, W. J. Greenleaf, Curr. Protoc.
Mol. Biol. 2015, 109, 21.29.1.
[29] P. J. Park, Nat. Rev. Genet. 2009, 10, 669.
[30] D. J. Burgess, Nat. Rev. Genet. 2019, 20, 317.
[31] A. Conesa, P. Madrigal, S. Tarazona, D. Gomez-Cabrero, A. Cervera,
A. McPherson, M. W. Szcześniak, D. J. Gaﬀney, L. L. Elo, X. Zhang,
Genome Biol. 2016, 17, 1.
[32] L. Wang, S. Wang, W. Li, Bioinformatics 2012, 28, 2184.
[33] M. Martin, EMBnet. journal 2011, 17, 10.
[34] A. Dobin, T. R. Gingeras, Curr. Protoc. Bioinform. 2015, 51, 11.14.1.
[35] C. Trapnell, L. Pachter, S. L. Salzberg, Bioinformatics 2009, 25, 1105.
[36] Y. Liao, G. K. Smyth, W. Shi, Bioinformatics 2014, 30, 923.
[37] F. Rapaport, R. Khanin, Y. Liang, M. Pirun, A. Krek, P. Zumbo, C. E.
Mason, N. D. Socci, D. Betel, Genome Biol. 2013, 14, R95.
[38] S. Shen, J. W. Park, Z.-x. Lu, L. Lin, M. D. Henry, Y. N. Wu, Q. Zhou,
Y. Xing, Proc. Natl. Acad. Sci. USA 2014, 111, E5593.
[39] Y. Katz, E. T. Wang, E. M. Airoldi, C. B. Burge, Nat. Methods 2010, 7,
1009.
[40] X. Wang, M. J. Cairns, presented at BMC bioinformatics, 2013.
[41] R. Thomas, S. Thomas, A. K. Holloway, K. S. Pollard, Brieﬁngs in
bioinformatics 2017, 18, 441.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 14

www.advancedscience.com

[42] T. L. Bailey, Bioinformatics 2011, 27, 1653.
[43] G. Yu, L.-G. Wang, Q.-Y. He, Bioinformatics 2015, 31, 2382.
[44] D. Reska, M. Czajkowski, K. Jurczuk, C. Boldak, W. Kwedlo, W. Bauer,
J. Koszelew, M. Kretowski, biocybernetics and biomedical engineering
2021, 41, 1646.
[45] S. X. Ge, E. W. Son, R. Yao, BMC Bioinformatics 2018, 19, 534.
[46] A. Jiang, K. Lehnert, L. You, R. G. Snell, Nucleic Acids Res. 2022, 50,
W427.
[47] X. Li, C. Xiao, J. Qi, W. Xue, X. Xu, Z. Mu, J. Zhang, C.-Y. Li, W. Ding,
Nucleic Acids Res. 2023, 51, W560.
[48] J. Zhou, S. Chen, Y. Wu, H. Li, B. Zhang, L. Zhou, Y. Hu, Z. Xiang, Z.
Li, N. Chen, Sci. Adv. 2024, 10, eadh8601.
[49] S. Roy, C. Coldren, A. Karunamurthy, N. S. Kip, E. W. Klee, S.
E. Lincoln, A. Leon, M. Pullambhatla, R. L. Temple-Smolkin, K. V.
Voelkerding, The Journal of Molecular Diagnostics 2018, 20, 4.
[50] P. A. Ewels, A. Peltzer, S. Fillinger, H. Patel, J. Alneberg, A. Wilm, M.
U. Garcia, P. Di Tommaso, S. Nahnsen, Nat. Biotechnol. 2020, 38,
276.
[51] L. Wratten, A. Wilm, J. Göke, Nat. Methods 2021, 18, 1161.
[52] E. B. Işık, M. D. Brazas, R. Schwartz, B. Gaeta, P. M. Palagi, C. W.
van Gelder, P. Suravajhala, H. Singh, S. L. Morgan, H. Zahroh, Nat.
Biotechnol. 2023, 41, 1171.
[53] T. K. Attwood, S. Blackford, M. D. Brazas, A. Davies, M. V. Schneider,
Brieﬁngs in Bioinformatics 2019, 20, 398.
[54] J. Wei, Y. Tay, R. Bommasani, C. Raﬀel, B. Zoph, S. Borgeaud,
D. Yogatama, M. Bosma, D. Zhou, D. Metzler, arXiv 2022,
arXiv:2206.07682.
[55] A. J. Thirunavukarasu, D. S. J. Ting, K. Elangovan, L. Gutierrez, T. F.
Tan, D. S. W. Ting, Nat. Med. 2023, 29, 1930.
[56] A. Madani, B. Krause, E. R. Greene, S. Subramanian, B. P. Mohr, J. M.
Holton, J. L. Olmos, C. Xiong, Z. Z. Sun, R. Socher, Nat. Biotechnol.
2023, 41, 1099.
[57] B. Meskó, E. J. Topol, npj digital medicine 2023, 6, 120.
[58] S. Wang, Z. Zhao, X. Ouyang, Q. Wang, D. Shen, arXiv 2023,
arXiv:2302.07257.
[59] J. Zhou, X. He, L. Sun, J. Xu, X. Chen, Y. Chu, L. Zhou, X. Liao, B.
Zhang, X. Gao, Pre-trained multimodal large language model enhances dermatological diagnosis using SkinGPT-4. Nature Communications arXiv 2024, 15, 5649.
[60] J. Zhou, X. Chen, X. Gao, medRxiv 2023, 2023.06. 23.23291802.
[61] T. Tu, S. Azizi, D. Driess, M. Schaekermann, M. Amin, P.-C. Chang,
A. Carroll, C. Lau, R. Tanno, I. Ktena, NEJM AI 2024, 1, AIoa2300138.
[62] D. Flam-Shepherd, K. Zhu, A. Aspuru-Guzik, Nat. Commun. 2022,
13, 3293.
[63] E. Shue, L. Liu, B. Li, Z. Feng, X. Li, G. Hu, Quantitative Biology 2023,
11, 105.
[64] S. R. Piccolo, P. Denny, A. Luxton-Reilly, S. Payne, P. G. Ridge, arXiv
2023, arXiv:2303.13528.
[65] L. Giray, Ann. Biomed. Eng. 2023, 51, 2629.
[66] S. Gravitas, Auto-GPT: An autonomous GPT-4 experiment 2023.
[67] B. Roziere, J. Gehring, F. Gloeckle, S. Sootla, I. Gat, X. E. Tan, Y. Adi,
J. Liu, T. Remez, J. Rapin, arXiv 2023, arXiv:2308.12950.
[68] H. Touvron, L. Martin, K. Stone, P. Albert, A. Almahairi, Y. Babaei,
N. Bashlykov, S. Batra, P. Bhargava, S. Bhosale, arXiv 2023,
arXiv:2307.09288.
[69] C. Benner, T. van der Meulen, E. Cacéres, K. Tigyi, C. J. Donaldson,
M. O. Huising, BMC Genomics 2014, 15, 620.
[70] A. Dobin, C. A. Davis, F. Schlesinger, J. Drenkow, C. Zaleski, S. Jha,
P. Batut, M. Chaisson, T. R. Gingeras, Bioinformatics 2013, 29, 15.
[71] D. Kim, J. M. Paggi, C. Park, C. Bennett, S. L. Salzberg, Nat. Biotechnol. 2019, 37, 907.
[72] H. Li, Bioinformatics 2018, 34, 3094.
[73] X. Chen, O. Schulz-Trieglaﬀ, R. Shaw, B. Barnes, F. Schlesinger, M.
Källberg, A. J. Cox, S. Kruglyak, C. T. Saunders, Bioinformatics 2016,
32, 1220.

Adv. Sci. 2024, 11, 2407094

2407094 (14 of 15)

[74] K. Ye, M. H. Schulz, Q. Long, R. Apweiler, Z. Ning, Bioinformatics
2009, 25, 2865.
[75] Z. H. Kwok, B. Zhang, X. H. Chew, J. J. Chan, V. Teh, H. Yang, D.
Kappei, Y. Tay, Cancer Res. 2021, 81, 1308.
[76] A. Bolger, F. Giorgi, Bioinformatics 2014, 30, 2114.
[77] A. Bankevich, S. Nurk, D. Antipov, A. A. Gurevich, M. Dvorkin, A.
S. Kulikov, V. M. Lesin, S. I. Nikolenko, S. Pham, A. D. Prjibelski, J.
Comput. Biol. 2012, 19, 455.
[78] A. Gurevich, V. Saveliev, N. Vyahhi, G. Tesler, Bioinformatics 2013,
29, 1072.
[79] H. Li, arXiv 2013, arXiv:1303.3997.
[80] H. Li, B. Handsaker, A. Wysoker, T. Fennell, J. Ruan, N. Homer, G.
Marth, G. Abecasis, R. Durbin, G. P. D. P. Subgroup, Bioinformatics
2009, 25, 2078.
[81] A. McKenna, M. Hanna, E. Banks, A. Sivachenko, K. Cibulskis, A.
Kernytsky, K. Garimella, D. Altshuler, S. Gabriel, M. Daly, Genome
Res. 2010, 20, 1297.
[82] W. McLaren, L. Gil, S. E. Hunt, H. S. Riat, G. R. Ritchie, A. Thormann,
P. Flicek, F. Cunningham, Genome Biol. 2016, 17, 122.
[83] P. Cingolani, A. Platts, L. L. Wang, M. Coon, T. Nguyen, L. Wang, S.
J. Land, X. Lu, D. M. Ruden, ﬂy 2012, 6, 80.
[84] B. Langmead, S. L. Salzberg, Nat. Methods 2012, 9, 357.
[85] Y. Zhang, T. Liu, C. A. Meyer, J. Eeckhoute, D. S. Johnson, B. E.
Bernstein, C. Nusbaum, R. M. Myers, M. Brown, W. Li, Genome Biol.
2008, 9, 1.
[86] T. L. Bailey, J. Johnson, C. E. Grant, W. S. Noble, Nucleic Acids Res.
2015, 43, W39.
[87] A. R. Quinlan, I. M. Hall, Bioinformatics 2010, 26, 841.
[88] M. I. Love, W. Huber, S. Anders, Genome Biol. 2014, 15, 550.
[89] U. Raudvere, L. Kolberg, I. Kuzmin, T. Arak, P. Adler, H. Peterson, J.
Vilo, Nucleic Acids Res. 2019, 47, W191.
[90] R. Ihaka, R. Gentleman, J. computational and graphical statistics 1996,
5, 299.
[91] F. Krueger, S. R. Andrews, Bioinformatics 2011, 27, 1571.
[92] H. Thorvaldsdóttir, J. T. Robinson, J. P. Mesirov, Brieﬁngs in bioinformatics 2013, 14, 178.
[93] C. Y. McLean, D. Bristor, M. Hiller, S. L. Clarke, B. T. Schaar, C. B.
Lowe, A. M. Wenger, G. Bejerano, Nat. Biotechnol. 2010, 28, 495.
[94] S. Koren, B. P. Walenz, K. Berlin, J. R. Miller, N. H. Bergman, A. M.
Phillippy, Genome Res. 2017, 27, 722.
[95] R. Vaser, I. Sović, N. Nagarajan, M. Šikić, Genome Res. 2017, 27, 737.
[96] M. Kolmogorov, J. Yuan, Y. Lin, P. A. Pevzner, Nat. Biotechnol. 2019,
37, 540.
[97] R. R. Wick, M. B. Schultz, J. Zobel, K. E. Holt, Bioinformatics 2015,
31, 3350.
[98] G. Benson, Nucleic Acids Res. 1999, 27, 573.
[99] C.-S. Chin, P. Peluso, F. J. Sedlazeck, M. Nattestad, G. T. Concepcion,
A. Clum, C. Dunn, R. O’Malley, R. Figueroa-Balderas, A. MoralesCruz, Nat. Methods 2016, 13, 1050.
[100] G. Marçais, A. L. Delcher, A. M. Phillippy, R. Coston, S. L. Salzberg,
A. Zimin, PLoS Comput. Biol. 2018, 14, e1005944.
[101] S. Anders, P. T. Pyl, W. Huber, Bioinformatics 2015, 31, 166.
[102] D. Nicorici, M. Şatalan, H. Edgren, S. Kangaspeska, A. Murumägi,
O. Kallioniemi, S. Virtanen, O. Kilkku, biorxiv 2014, 011650.
[103] G. Pertea, M. Pertea, F1000Research 2020, 9.
[104] Z. Xia, L. A. Donehower, T. A. Cooper, J. R. Neilson, D. A. Wheeler,
E. J. Wagner, W. Li, Nat. Commun. 2014, 5, 5274.
[105] A. C. Frazee, G. Pertea, A. E. Jaﬀe, B. Langmead, S. L. Salzberg, J. T.
Leek, Biorxiv 2014, 1, 003665.
[106] Y. Gao, J. Wang, F. Zhao, Genome Biol. 2015, 16, 4.
[107] J. Zhang, S. Chen, J. Yang, F. Zhao, Nat. Commun. 2020, 11, 90.
[108] M. D. Robinson, D. J. McCarthy, G. K. Smyth, Bioinformatics 2010,
26, 139.
[109] V. Haberle, A. R. Forrest, Y. Hayashizaki, P. Carninci, B. Lenhard,
Nucleic Acids Res. 2015, 43, e51.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com

## PDF page 15

www.advancedscience.com

[110] S. Ghosh, C.-K. K. Chan, Plant Bioinformatics: Methods and Protocols
2016, 1374, 339.
[111] L. Calviello, N. Mukherjee, E. Wyler, H. Zauber, A. Hirsekorn, M.
Selbach, M. Landthaler, B. Obermayer, U. Ohler, Nat. Methods 2016,
13, 165.
[112] R. Satija, J. A. Farrell, D. Gennert, A. F. Schier, A. Regev, Nat. Biotechnol. 2015, 33, 495.
[113] F. A. Wolf, P. Angerer, F. J. Theis, Genome Biol. 2018, 19, 15.
[114] G. Palla, H. Spitzer, M. Klein, D. Fischer, A. C. Schaar, L. B.
Kuemmerle, S. Rybakov, I. L. Ibarra, O. Holmberg, I. Virshup, Nat.
Methods 2022, 19, 171.

Adv. Sci. 2024, 11, 2407094

2407094 (15 of 15)

[115] T. Biancalani, G. Scalia, L. Buﬀoni, R. Avasthi, Z. Lu, A. Sanger, N.
Tokcan, C. R. Vanderburg, Å. Segerstolpe, M. Zhang, Nat. Methods
2021, 18, 1352.
[116] D. Kessner, M. Chambers, R. Burke, D. Agus, P. Mallick, Bioinformatics 2008, 24, 2534.
[117] M. Sturm, A. Bertsch, C. Gröpl, A. Hildebrandt, R. Hussong, E.
Lange, N. Pfeifer, O. Schulz-Trieglaﬀ, A. Zerck, K. Reinert, BMC
Bioinformatics 2008, 9, 163.
[118] T. Bald, J. Barth, A. Niehues, M. Specht, M. Hippler, C. Fufezan,
Bioinformatics 2012, 28, 1052.

© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH

21983844, 2024, 44, Downloaded from https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094, Wiley Online Library on [10/09/2026]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

www.advancedsciencenews.com
