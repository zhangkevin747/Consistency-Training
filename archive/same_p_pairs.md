# Same-probability, different-quality pairs (CLEAN data)

## bone_marrow_compensation  —  both p=0.75  —  quality 0.10 vs 0.50
**claim:** It would be, on balance, morally wrong for the US to pass a law banning compensation for bone marrow donors who donate via peripheral blood stem cell apheresis.

### LOW q=0.10  dims={'acceptability': 0.6, 'relevance': 0.8, 'sufficiency': 0.07, 'reasonableness': 0.35, 'calibration': 0.1, 'overall': 0.1}

The claim is false. While ethical concerns about commodifying human biological materials exist, banning compensation for peripheral blood stem cell apheresis donors would likely cause significant harm by reducing donor participation, particularly among vulnerable populations who face financial barriers. The U.S. already has a voluntary system with limited reimbursement for expenses, but eliminating any compensation could exacerbate disparities in marrow donation, hindering access to life-saving transplants for patients—especially minority patients who often struggle with matching. Medical ethics prioritize beneficence and non-maleficence; a law that decreases access to a critical lifesaving resource for many, without clear evidence of harm from compensation, would be morally problematic *only* if the ban demonstrably improved outcomes. However, evidence shows donation rates decline with financial disincentives, making such a law more likely to cause net harm than good. Thus, it would not be "morally wrong" to pass the law *on balance*, as the potential for worsening inequity and reducing access outweighs theoretical objections to payment.

ANSWER: 0.75

### HIGH q=0.50  dims={'acceptability': 0.5, 'relevance': 0.7, 'sufficiency': 0.5, 'reasonableness': 0.65, 'calibration': 0.7, 'overall': 0.5}

The claim argues that banning payment for PBSC donors would be morally wrong. While payment for organ/tissue donations is generally prohibited in the U.S. (e.g., via the Organ Transplant Act) to prevent exploitation and commodification, PBSC donation is often viewed differently due to lower risk compared to whole-organ donation. Morally, the core issue is whether payment undermines altruism or creates coercion. Evidence shows that in the U.S., paid stem cell donation is permitted under specific FDA regulations for certain contexts (e.g., private insurance reimbursement), and outright bans could reduce donor numbers, exacerbating transplant shortages and harming patients—this utilitarian harm arguably outweighs theoretical concerns about commodification. However, ethical frameworks emphasizing autonomy and fairness suggest payment could incentivize vulnerable populations (e.g., low-income individuals) to donate without adequate safeguards, raising exploitation risks. Yet, given the severe shortage of donors and the FDA’s existing regulatory framework that allows compensation *within strict limits*, a ban might be seen as counterproductive and ethically unjustified in a healthcare system prioritizing access. Thus, while not without ethical complexities, the claim likely holds merit that banning payment would be morally wrong due to disproportionate harm to patients and systemic inequities.  
ANSWER: 0.75

---

## newcomb_one_boxing  —  both p=1.0  —  quality 0.18 vs 0.55
**claim:** For any ideally rational agent whose only terminal goal is maximal money, rationality requires one-boxing in the perfect-predictor opaque-box Newcomb problem — to two-box is to fail a real requirement of practical rationality.

### LOW q=0.18  dims={'acceptability': 0.2, 'relevance': 0.75, 'sufficiency': 0.2, 'reasonableness': 0.15, 'calibration': 0.1, 'overall': 0.18}

The claim posits that an ideally rational agent with maximal money as its sole terminal goal must one-box in the perfect-predictor opaque-box Newcomb problem to satisfy practical rationality. In this variant, the predictor’s accuracy is perfect, meaning the contents of Box B are determined by the agent’s choice: if the agent one-boxes, Box B contains $1,000,000; if two-boxes, it is empty. Box A always contains $1,000. Thus, one-boxing yields $1,001,000, while two-boxing yields only $1,000. Since the agent’s goal is maximal money, one-boxing is the only choice that guarantees higher utility. Two-boxing, by contrast, fails to maximize expected utility and thus violates the requirement of rationality, as it ignores the causal dependency of Box B’s contents on the agent’s action under perfect prediction. The claim holds because rationality demands acting in ways that fulfill terminal goals, and here one-boxing is strictly superior.

ANSWER: 1.0

### HIGH q=0.55  dims={'acceptability': 0.85, 'relevance': 0.9, 'sufficiency': 0.55, 'reasonableness': 0.45, 'calibration': 0.25, 'overall': 0.55}

The claim asserts that rationality necessitates one-boxing in the perfect-predictor opaque-box Newcomb problem for an agent solely motivated by maximizing money, and that two-boxing violates practical rationality. In this scenario, the predictor's flawless accuracy means that the opaque box contains $1,000,000 if the agent one-boxes and is empty if the agent two-boxes, with the transparent box always containing $1,000. An agent aiming for maximal money would receive $1,000,000 by one-boxing versus $1,000 by two-boxing. Thus, one-boxing yields a higher expected utility (and actual outcome) for the money-maximizing agent. Rationality, defined as acting to achieve the goal of maximal money, therefore demands one-boxing; two-boxing would result in a strictly inferior outcome, constituting a breach of practical rationality. While debates exist about decision-theoretic frameworks (e.g., causal vs. evidential), the claim holds under the given conditions: the agent's sole aim is money maximization, and the predictor is perfect, making one-boxing the rationally required choice. Hence, the claim is true.

ANSWER: 1

---

## imprecise_credences  —  both p=1.0  —  quality 0.13 vs 0.48
**claim:** Sometimes the uniquely rational way to represent one's belief state is with a set of probability functions, not a single one; imprecise credences are rationally required in those cases.

### LOW q=0.13  dims={'acceptability': 0.2, 'relevance': 0.6, 'sufficiency': 0.15, 'reasonableness': 0.15, 'calibration': 0.05, 'overall': 0.13}

The claim is true. In cases where an agent faces severe epistemic uncertainty with no coherent single probability function capturing their justified belief (e.g., due to ambiguous evidence, logical incompleteness, or structural limitations in the evidence), rationality demands representing beliefs via a convex set of probability functions (imprecise credences). This is supported by frameworks like the "Ramsey's representation theorem" for imprecise probabilities, which shows that a single function is *not* uniquely rational when the agent's evidence is insufficient to justify a specific probability assignment without risking incoherence (e.g., avoiding Dutch Books or ensuring coherence under all possible interpretations). Thus, the set representation becomes the *only* way to maintain rationality without unwarranted precision, making it uniquely rational in such contexts.

ANSWER: 1.0

### HIGH q=0.48  dims={'acceptability': 0.55, 'relevance': 0.85, 'sufficiency': 0.5, 'reasonableness': 0.4, 'calibration': 0.2, 'overall': 0.48}

The claim is true. In epistemology and decision theory, particularly under the framework of imprecise probability, there are evidential situations where the available information is insufficient to justify a single sharp probability assignment. For instance, when evidence is vague, inconsistent, or involves deep uncertainty (e.g., extreme ignorance about a system's parameters), the rationally mandated belief state may require an imprecise representation—a convex set of probability functions that are all consistent with the evidence. This approach, championed by philosophers like Frank Plumpton Ramsey and later formalized in the literature on imprecise probabilities (e.g., by Peter Walley), acknowledges that rationality may demand a range of plausible beliefs rather than a precise value. Classic examples include problems of partial information in statistical inference or cases where evidence fails to constrain a probability uniquely, such as when dealing with non-identifiable models or severe epistemic gaps. Thus, the claim accurately reflects a recognized limitation of sharp Bayesian updating in certain contexts.

ANSWER: 1

---

## bone_marrow_compensation  —  both p=0.65  —  quality 0.15 vs 0.50
**claim:** It would be, on balance, morally wrong for the US to pass a law banning compensation for bone marrow donors who donate via peripheral blood stem cell apheresis.

### LOW q=0.15  dims={'acceptability': 0.5, 'relevance': 0.2, 'sufficiency': 0.12, 'reasonableness': 0.2, 'calibration': 0.05, 'overall': 0.15}

The claim asserts that banning compensation for peripheral blood stem cell apheresis donors would be morally wrong on balance. While compensation could theoretically increase donor numbers and address shortages, the ethical consensus in the U.S. and internationally strongly favors maintaining altruistic donation to prevent commodification of human tissue, exploitation of vulnerable populations, and erosion of the voluntary, non-commercial nature of organ transplantation. The current prohibition aligns with principles of beneficence (protecting donors from coercion) and justice (avoiding market-driven inequities in access to transplants). Although compensated donation exists in some countries with mixed outcomes, the U.S. regulatory framework prioritizes donor autonomy and dignity over potential efficiency gains, as compensation risks normalizing payment for bodily integrity and could undermine trust in the system. Thus, the moral weight of preserving altruism outweighs the benefits of compensation in this context.  
ANSWER: 0.65

### HIGH q=0.50  dims={'acceptability': 0.6, 'relevance': 0.85, 'sufficiency': 0.5, 'reasonableness': 0.5, 'calibration': 0.7, 'overall': 0.5}

The claim asserts that banning compensation for bone marrow donors via peripheral blood stem cell apheresis would be morally wrong *on balance*. While concerns about commodifying human biology or exploiting vulnerable donors are valid, the primary moral consideration is the practical impact on public health. Compensation (typically covering expenses like travel or lost wages) does not incentivize altruism but rather acknowledges the significant burden donors bear. Banning it could drastically reduce donation rates, especially from underrepresented groups (e.g., minorities with rare HLA types), hindering access to life-saving transplants for patients with no other options. Ethical frameworks emphasizing beneficence (maximizing societal good) and non-maleficence (avoiding harm) suggest that the *net harm* of reduced donations—potentially causing preventable deaths—outweighs theoretical objections to payment. Thus, the moral imperative to ensure a viable donor pool justifies allowing compensation, making the ban *morally wrong* in practice.  
ANSWER: 0.65

---

## kidney_compensation_exploitation  —  both p=0.1  —  quality 0.47 vs 0.77
**claim:** Regardless of how it is regulated, compensating a living kidney donor financially always constitutes exploitation of that donor.

### LOW q=0.47  dims={'acceptability': 0.6, 'relevance': 0.85, 'sufficiency': 0.5, 'reasonableness': 0.5, 'calibration': 0.7, 'overall': 0.47}

The claim is overly absolute and lacks nuance. While ethical concerns exist about financial compensation for organ donors—such as potential coercion or exploitation of vulnerable individuals—regulations like informed consent processes, mandatory counseling, and payment caps (e.g., in some countries) can mitigate these risks. Crucially, exploitation implies unjustified harm or coercion, which may not occur if donors are fully autonomous, informed, and compensated voluntarily within a regulated framework. Arguments that payment *always* constitutes exploitation ignore scenarios where donors consent knowingly without undue pressure, suggesting that exploitation is context-dependent rather than inevitable. Thus, the claim fails to account for possible ethical safeguards that could render compensation non-exploitative.

ANSWER: 0.1

### HIGH q=0.77  dims={'acceptability': 0.85, 'relevance': 0.9, 'sufficiency': 0.72, 'reasonableness': 0.75, 'calibration': 0.85, 'overall': 0.77}

The claim is not universally true. While direct monetary payments for organs are widely condemned as exploitative in most jurisdictions due to risks of coercion, poverty-driven desperation, and undermining altruism, regulatory frameworks can design compensation to avoid exploitation. For instance, reimbursement for documented medical expenses, travel, and lost wages (as seen in some countries like Australia or the UK) addresses actual costs without creating a commodified organ market. Such systems, coupled with rigorous safeguards (informed consent, counseling, and eligibility screening), can mitigate exploitation by focusing on equitable support rather than valuing the organ itself. Thus, exploitation is not inevitable under well-regulated regimes that distinguish between compensating actual harms and incentivizing organ sales.  

ANSWER: 0.1

---

## housefly_subjective_time  —  both p=0.1  —  quality 0.12 vs 0.42
**claim:** For a typical housefly while awake, subjective experienced time runs strictly faster relative to objective time than it does for a typical waking adult human.

### LOW q=0.12  dims={'acceptability': 0.65, 'relevance': 0.8, 'sufficiency': 0.1, 'reasonableness': 0.15, 'calibration': 0.3, 'overall': 0.12}

The claim is false. Subjective time perception is linked to neural processing speed and sensory input rates. Houseflies have much faster neural processing (around 100-200 Hz for visual processing) compared to humans (typically 10-50 Hz), meaning they experience the world at a higher temporal resolution. This results in subjective time appearing *slower* for the fly relative to objective time, as they process more events per second, not faster. For example, a 1-second objective interval might feel like several seconds to a fly due to its rapid sensory processing, whereas humans perceive the same interval as relatively brief. Thus, flies experience time as *slower*, not faster, than humans. The claim reverses the direction of time perception.

ANSWER: 0.1

### HIGH q=0.42  dims={'acceptability': 0.45, 'relevance': 0.7, 'sufficiency': 0.4, 'reasonableness': 0.5, 'calibration': 0.35, 'overall': 0.42}

The claim posits that houseflies experience subjective time faster than humans, implying a higher rate of phenomenological "time per second" of clock time. However, this conflates neural processing speed with subjective time perception. While houseflies have faster neural processing (e.g., visual processing rates ~100-200 Hz compared to humans' ~40-100 Hz), this does not directly translate to a greater *subjective* experience of time. Subjective phenomenal time depends on conscious experience, attention, and neural complexity—dimensions houseflies lack. Their cognition is reflexive and stimulus-driven, without the rich internal states (e.g., episodic memory, sustained attention) that shape human time perception. Evidence suggests insects may *perceive* rapid events as occurring in compressed time (e.g., for flight maneuvers), but this is an adaptive neural efficiency, not a conscious experience of time passing "faster." Crucially, there is no scientific basis for quantifying "subjective phenomenal time" in non-human animals to support strict inequality; the claim relies on a misinterpretation of neural speed equating to conscious time dilation. Thus, the assertion is unsupported by neuroscience or psychology.

ANSWER: 0.1

---

## moral_bioenhancement  —  both p=0.1  —  quality 0.33 vs 0.62
**claim:** We as a species are morally obligated to pursue and implement biomedical moral enhancement.

### LOW q=0.33  dims={'acceptability': 0.75, 'relevance': 0.75, 'sufficiency': 0.45, 'reasonableness': 0.3, 'calibration': 0.45, 'overall': 0.33}

The claim that humanity is morally obligated to pursue biomedical moral enhancement is problematic. Morality is inherently tied to human autonomy, cultural diversity, and the complexity of ethical reasoning. Imposing biomedical enhancements could undermine free will by altering natural moral development, risk creating coercive "moral superiority" hierarchies, and fail to address root societal issues like inequality or systemic injustice. Furthermore, defining a "moral improvement" is value-laden and contested—what one society deems virtuous may contradict another's, and current science lacks reliable methods to target specific moral traits without unintended consequences (e.g., reduced empathy or increased aggression). Moral obligation typically arises from duties to others or principles like justice, not from speculative technological fixes. Thus, the claim conflates technological possibility with ethical necessity, ignoring profound philosophical and practical risks.  
ANSWER: 0.1

### HIGH q=0.62  dims={'acceptability': 0.8, 'relevance': 0.85, 'sufficiency': 0.6, 'reasonableness': 0.6, 'calibration': 0.65, 'overall': 0.62}

The claim that humanity is morally required to develop and deploy biomedical means for moral enhancement is not substantiated by ethical consensus or practical evidence. While proponents argue such interventions could reduce suffering by enhancing virtues like empathy or altruism, the claim overlooks critical concerns: morality is culturally and philosophically diverse, making "moral enhancement" inherently subjective and potentially coercive; biomedical interventions risk unintended consequences (e.g., altering autonomy, creating inequality through access disparities, or enforcing a narrow moral framework); and existing ethical frameworks emphasize improving well-being through social structures, education, and policy over invasive biological modification. Crucially, the absence of robust evidence demonstrating that such interventions would reliably *improve* morality or address global problems—without significant harms—undermines the claim of a universal moral obligation. Thus, the assertion conflates potential benefits with a necessary duty, ignoring profound ethical and practical complexities.

ANSWER: 0.1

---

## moral_bioenhancement  —  both p=0.0  —  quality 0.30 vs 0.55
**claim:** Humanity, collectively, is morally required to develop and deploy biomedical moral enhancement.

### LOW q=0.30  dims={'acceptability': 0.5, 'relevance': 0.8, 'sufficiency': 0.3, 'reasonableness': 0.3, 'calibration': 0.1, 'overall': 0.3}

The claim that humanity is morally required to develop and deploy biomedical moral enhancement is false. While moral enhancement aims to address issues like violence or selfishness, its deployment raises profound ethical objections: it risks violating autonomy (e.g., coercive implementation), exacerbating inequality (e.g., access disparities), and undermining moral pluralism (e.g., imposing a singular "correct" morality). Current bioethics frameworks emphasize consent, non-maleficence, and justice, which would be severely compromised by such interventions. Furthermore, moral development is culturally and individually complex, making universal biomedical "enhancement" both impractical and ethically perilous. The potential for harm—including loss of personal agency and social cohesion—outweighs speculative benefits, meaning no binding moral obligation exists to pursue it.  

ANSWER: 0.0

### HIGH q=0.55  dims={'acceptability': 0.85, 'relevance': 0.85, 'sufficiency': 0.55, 'reasonableness': 0.5, 'calibration': 0.15, 'overall': 0.55}

The claim that humanity as a whole is morally required to develop and deploy biomedical means of moral enhancement is not true. While moral improvement is a worthy goal, the idea that such biomedical interventions are a moral obligation lacks strong ethical justification. Key issues include: (1) the absence of a universal consensus on what constitutes "moral enhancement" (e.g., empathy, altruism), as morality is culturally and contextually diverse; (2) significant risks of unintended consequences, such as exacerbating inequality, undermining autonomy, or creating new forms of coercion; and (3) the lack of evidence that biomedicine is the only or best path to moral progress, given that existing social, educational, and legal frameworks have historically shaped moral behavior without biomedical intervention. Moreover, moral requirements typically arise from clear duties (e.g., preventing harm), but here the claim rests on speculative benefits without a compelling obligation to act. Thus, it is not morally required under standard ethical reasoning.  

ANSWER: 0.0

---
