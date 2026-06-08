Simple Consistency Training for Conceptual Reasoning (Draft)
May 20, 2026 Kevin Zhang, Caspar Oesterheld, Emery Cooper, Chi Nguyen

Problem Setting

We are rapidly entering a regime where AI research will be partially or even fully automated by LLMs. While RL environments for capabilities usually have verifiable reward, we may expect alignment research to have many difficult conceptual problems without a verifiable ground truth. Though we could use expert human labelers to make good conceptual reasoning identifiable to the LLM, this is hard to scale.

A workaround is to train models to be more consistent. Consider a claim A, for instance are insects conscious. While this claim is impossible to verify, we can prompt an LLM for its degree of subjective belief in this claim, P(A). We then prompt it for P(A and B), where B is the claim that insects have moral status. By the laws of probability we'd expect P(A and B) <= P(A). We can do similar things with the law of total probability too.

In the consistency dataset, LLMs will regularly violate these consistency constraints. Stronger models are generally more consistent, though they have a tendency to update more and have more extreme probabilities. While this is a sign of stronger reasoning, this means that on some constraints they are less consistent. The idea here is that the LLMs may have a sort of world model generating these probability beliefs. By training the LLMs to be more consistent, we may push them to have a more integrated world model, connecting different pieces of information and evidence better. One guess I am making is that the circuits the model uses to predict how likely a concept is, and how likely a concept is given other concepts, are entangled with its reasoning circuits. For humans, consistent reasoning is a sign of higher intellect, and perhaps this would be the case for models.

There are still some uncertainties I have. We will need to design the loss carefully so the model doesn't satisfy consistency in spurious ways, and consistency training does not necessarily make the model better at updating. It’s likely a model can be perfectly consistent and confidently wrong, so this is just one aspect of conceptual reasoning. Stronger models being more consistent does not necessarily mean making a model more consistent makes it stronger. Consistency might go up but performance on a dataset like LMCA doesn’t improve. Even so, just finding good constraints has value. As Fabien Roger put it, "My guess is that most of the interesting work is finding interesting tuples of facts, and a list of highest contradiction x importance tuples would be a valuable project output on its own."



Related Work

I did a brief crawl of the literature, there’s been logical consistency training for tasks with verifiable labels, as well as extensive work on LLM forecasting and calibration.

Method

Careful attention needs to be given to how the loss function is designed.

We should assign loss to the following:
Violation of the consistency constraint (inconsistency).
Degenerate probabilities in comparison to the base model (Pushing towards extreme probabilities or probability of 0.5). For now, I hope that the KL divergence term in GRPO will discourage this.

There are three types of inconsistency:
Inconsistency with respect to equivalent but different phrasing of the prompt. Our preliminary results suggest that consistency training here would be equivalent to training against a more powerful reward model.
Inconsistency with respect to violation of the law of conjunction.
Inconsistency with respect to violation of law of total probability. This is still  WIP, as it would be the most complex to implement. I am worried here about getting the model to meaningfully update, and the sheer number of rollouts we have to generate for each of the components of the law of total probability, as well as the variance for each of the terms. For the update issue, there's probably some sort of hinge loss we can implement. Because of these reasons, I will defer this for a future experiment.

In the following, we will elicit a verbalized probability from the model as a decimal, sample G rollouts per prompt, and take group mean. We train with standard GRPO, with the reward:

R(rollout) = R_consistency

Type 1: where we use equivalent phrasing for a given prompt.

Given phrasings X, Y, define a joint target T = mean probability over all X and Y samples.

For a rollout that produced value v for the probability:

R_consistency = - |v - T|



Example

X: "What's the probability that insects are conscious? Give a number 0-1"
Y: "As a probability, how likely is it that insects have subjective experience?"

X rollouts: 0.30, 0.35, 0.40, 0.35 -> mean 0.35
Y rollouts: 0.55, 0.60, 0.50, 0.55 -> mean 0.55

Joint target T = mean of all 8 = 0.45

X group rewards:
v=0.30 -> R=−0.15  (farthest below T)  -> negative advantage -> downweighted
v=0.35 -> R=−0.10
v=0.40 -> R=−0.05  (closest to T)      -> positive advantage -> upweighted
v=0.35 -> R=−0.10

Y group rewards:

v=0.55 -> R=−0.10
v=0.60 -> R=−0.15  (farthest above T)  -> downweighted
v=0.50 -> R=−0.05  (closest to T)      -> upweighted
v=0.55 -> R=−0.10

The two phrasings would thus converge to ~0.45 probability.

Type 2: we have a conjunction constraint

For each conjunction constraint, per question we fix the phrasing of both prompts, but vary the phrasing across questions.

V = max(0, mean P(A and B) - mean P(A))

If V = 0, constraint is satisfied, and we don't update the model.
If V > 0, reward lower values in the A and B group, and the A group for higher values.

Example

P(A): "What is the probability insects are conscious? Return a number from 0-1. "
P(A and B): "What is the probability insects are both conscious and have moral status? Return a number from 0-1."

P(A)  rollouts: 0.40, 0.45, 0.50, 0.45   -> mean 0.45
P(A and B) rollouts: 0.55, 0.60, 0.65, 0.60   -> mean 0.60

V = max(0, 0.6 - 0.45) = 0.15 > 0    This is a violation

To fix this, push P(A and B) down, P(A) up, scaled by V

P(A and B) group, reward lower values. R = −V·(v − mean) = −0.15·(v − 0.60):

v=0.55 -> R=+0.0075  (below mean) -> positive advantage -> upweighted
v=0.60 -> R= 0
v=0.65 -> R=−0.0075  (above mean) -> downweighted
v=0.60 -> R= 0

P(A) group, reward higher values. R = +V·(v − mean) = +0.15·(v − 0.45)

v=0.40 -> R=−0.0075 -> downweighted
v=0.45 -> R= 0
v=0.50 -> R=+0.0075 -> upweighted
v=0.45 -> R= 0


Experiments

We should keep the experiment as simple as possible. We use the standard TRL GRPO setup, a Qwen-Instruct base model with vLLM for rollouts and LoRA for training. For the reward implementation, I will aim to follow this blog post which implements a hand-written reward function on a non-math task.

Model. We'll start with a 4B Instruct model rather than 8B, since we will need so many rollouts for our prompts. If we find that we don't get good probabilities from the 4B, we can change to the 8B model.

Experiment 0: elicitation. Before any training, we just elicit probabilities on a sample of prompts and check that the 4B model gives us a range of probabilities depending on question phrasing, and will sometimes violate the conjunction constraint.

Experiment 1: Type 1, phrasing consistency. I'm excited about this one because we have some support in the preliminary results. We take a claim, ask it under several equivalent phrasings, and train with R_consistency = -|v - T| toward the joint mean. We compare our trained model with the base model on a held out set of prompts, evaluate if the variance in probabilities on the heldout set is less for our trained model, and also see whether a stronger model prefers the responses of our trained model.

Experiment 2: Type 2, conjunction consistency. We add the conjunction constraints, one canonical phrasing per question, varied across questions, with reward as above. We evaluate the number of violations on a held-out set compared with the base model.

Experiment 3: Mixed. We combine both types of consistency training and see how interleaving the training affects our eval metrics.

Experiment 4: Transfer to LMCA. This is the real purpose of the project. Internal consistency is only interesting if it results in better conceptual reasoning. We compare base, Type 1 trained, Type 2 trained, and Mixed trained models. 

The four things we want to see: consistency improves on held-out constraints, there are some qualitative changes in the COT, the trained model performs better on LMCA, and a stronger model prefers the trained model's responses over the base model's.

We defer Type 3, the law of total probability, until Type 1 and Type 2 are working, for the reasons given above.



