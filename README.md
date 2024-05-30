# Game Theory-Based Pricing Model for Public Transport and Autonomous Electric Vehicle Systems

## Overview

This repository contains a collection of Jupyter Notebooks and Python scripts to model and analyze the interactions between Public Transport (PT) operators, Shared Autonomous Electric Vehicle (SAEV) operators, and the government using game theory. The goal is to determine optimal pricing strategies under various scenarios, including tax policies, allowance policies, real-time pricing, rebalancing, and discharging options.

## Repository Structure

- 0430GameTheoryPricing
   - **GameTheoryPricingModel0430.ipynb**: Formulates the basic model parameters, variables, constraints, and utility functions for the game theory model.
- 0508GameTheoryPricing
   - **GameTheoryPricingModel0508.ipynb**: Extends the basic model to include environmental revenue and iterates over time periods to find the best pricing strategies for each period.
- 0514PublicTransport
   - **PTPayoffCalculation.ipynb**: Calculates the payoff for public transport operators, including ticket revenue, fleet investment, charging station cost, charging cost, maintenance cost, and tax cost.
- 0527Gaming
   - **public_transport_payoff.py**: Python script for calculating public transport payoffs.
   - **Gaming.ipynb**: Run this file to calculate and display results.
