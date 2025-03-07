# Kelley strategy

    Consider a gambler who, at each gamble, either wins or loses her bet with respective probabilities $p$ and $1 − p$. A popular gambling system known as the Kelley strategy is to always bet the fraction $2p − 1$ of your current fortune when $p > 12$. (See  S. Ross,  problem 7.67 p.378)

This is a simulation to explore the strategy of how large a “liquidity” reserve should one maintain when facing a stochastic prospect, e.g. what a cash reserve to hold for investment opportunities. An operational version of this would be to set allocate current sales inventory while keeping in reserve an amount for future sales. The current set-aside has a chance either to make or lose money, and that is a prime consideration for how much to set aside.

In an organization this simulates a group budgeting process, where at team must bet on opportunities that are at the same time both profitable but risky. The experience, when nature is inherently random, is the tradeoff between minimizing risk and not getting whipsawed by random events. 

## Hedging with a risky opportunity (“The Dice Game”)

- Purpose: Teach group risk taking; Elicit participants risk preferences.
- Situation: A management team periodically considers investment opportunities, starting with a fixed, shared budget. The  investment pays off before the next investment is offered.  The team is told that the payoff probability is fair, an estimate of the win probability is revealed. 
- Decision: At each round, the team must agree on a fraction of the current purse to invest in the current opportunity. The goal is to maximize the eventual winnings and not go broke. 
- Playing out the strategy: After several rounds, the team comes up with their investment rule. The rule could depend on the history of wins and losses.  Each team’s rule is evaluated by running it as a Kelly-strategy. 

## The Dice Game: Your task..

Your CEO called you to join an investment committee meeting along with 2 of your peers to make a go – no-go decision on an investment opportunity that just came to her attention.  These opportunities that arise periodically have proven to be good bets and will either payoff at 100% or fail entirely before the next opportunity comes up. You have a $1 million dollar fund for such investments that gets rolled back into the fund should the opportunity succeed. Your goal in this high-risk investment committee is  to maximize long-term value without going broke.  You expect to be part of this committee for the foreseeable future as the managers of a recurring stream of such one-shot investments. If it helps you, you can come up with a back-story on what these investments are. 

Your committee’s task is to decide as a team how much of your fund to invest in this opportunity.  The analyst who proposed the opportunity gave a credible estimate that it has a 70% chance of success, which is consistent with such opportunities your company has invested in, in the past. 

We will run this game interactively for 10 rounds where we track the running value of the investment fund.    Then your committee has to put together guidance – a formula – for managing the investment process that we will run in simulation into the future, to explore the expected return and variation of the strategy.  

## Take-aways from the Dice Game

1. Participants learn that invest too small a fraction, (risk aversion) and money is left on the table. Invest too large a fraction (risk seeking) and the strategy -> high variability and expected loss. 
2. By comparison with an optimal strategy (e.g. like a Kelly strategy), participants can understand that there is a rational approach that is better than “winging it.” 
3. The team’s agreed on investment fraction reveals their utility function’s risk preference (assuming log utility). 
4. The game can be diagrammed as an influence diagram, to introduce the concept

# Questions

* What is a risk-neutral strategy?  Is it an eventual loosing strategy with P = 1??
* For a constant fraction policy, the log increments are a biased random walk. The hitting times as a function of the policy tell the “lifetime” of the policy. 
* The win percentage estimation can assume a binomial –beta distribution closed form update. 
* A policy needs to estimate the win percentage from previous wins and losses.  If there were a choice among investments the problem would resemble a “multi-armed bandit”.  That would overload the demonstration. Better to keep it simple.  



