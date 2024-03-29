# SoWeiT-Connected

## Introduction
So far, only the connection between two buildings has been tested for the cross-building power exchange via direct lines. The integration of more than two buildings leads to new challenges.

In SoWeiT-connected - building on the findings from the WEIZconnected project - the on-site use of electricity from PV systems with direct lines for a network of several buildings is implemented. The system enables the optimization of the self-consumption of locally generated renewable energy as well as a common emergency power supply in the event of a failure of the public power supply. The requirements of the stakeholders are taken into account by means of co-creation processes. All components and business models are tested and validated using a demonstrator.

The results of the project are simulation models for the design and mapping of the system components, a demonstrator for the joint use of PV via direct lines, business models and billing systems taking into account the requirements of the users as well as statements regarding the system's multipliability.

Further information about the project is available at the homepage of [4ward Energy Research GmbH](https://www.4wardenergy.at/en/references/soweit-connected).

- ***Project Partner***

  - Municipality of Thannhausen

  - EOS Power Solutions GmbH

  - Weizer Energie- Innovations- Zentrum GmbH

  - Energienetze Steiermark GmbH

  - 4ward Energy Research GmbH

- ***Project-Duration:***  	10/2018 – 09/2021

- ***Funding program:***  	Stadt der Zukunft - 5th Call

- ***Funding authority:*** Bundestministerium für Verhehr, Innovation und Technologie

## Description

The direct line system in Thannhausen connects eight consumer with one photovoltaic system. Each consumer is connected to the direct line system as well as to the public grid. A control regime is needed, to decide whether a consumer is connected to the direct line system or the public grid. The program code the control regime is based on can be found in the function *SoWeiT_Connected_Optimierer.py*. A testing function *SoWeiT_Connected_Testfunktion.py* which calls the optimizer and calculates the switching process for two example days is available too.

For normal operation, the following rules apply for the control regime:

- First off, the consumption of the municipal buildings will be covered, only excess energy will be provided to the direct line system.

- The control unit will then check the power consumption values of the users and will sort them according to an internal ranking system so that most of the PV generation can be used directly. 

- Only users whose demand can be fully satisfied by the PV generation will be connected to the direct line system and separated from the public grid.
 
- The internal ranking system will ensure that over the course of a certain period distribution of PV generation will happen on a fair and transparent basis. 

- Any remaining excess PV generation will be fed into the public grid

To ensure the fair distribution of the PV generation between all users, the target function of the ranking system consists of two parts. The first part addresses the maximisation of the self-consumption within the direct line system, and the second part covers the equal distribution of the PV generation. Two weighting factors were used to determine, which part is more important for the ranking system. For the Thannhausen pilot a balanced setting was chosen, which ensures a fair distribution with only slight reductions of the self-consumption rate in comparison to the maximum possible one.

The equality of the distribution is controlled by applying a prioritising factor for each user in the target function of the optimisation algorithm, thus increasing or decreasing the importance of individual users. This factor is updated daily and reflects how much energy each user has already obtained from the direct line system. The user who got the lowest share of energy, in relation to his total energy demand by the time of the factor update gets the highest factor, and so one. A high factor means, that this user also has a higher priority for the optimiser. A low factor indicates that a user has already got a high relative share of energy in relation to the other users and therefore has a lower priority in the ranking system.

The optimisation is carried out every 15 seconds by the control system. To avoid a constant switching between the direct line system and the public grid a “clocking prevention” was implemented. This was necessary to prevent premature wear of the switching elements and increase the lifetime of the system. A certain switching contingent is available to the control system. If this switching contingent has been exceeded, users may be reconnected to the direct line system no earlier than five minutes after their switchover from the direct line system to the public grid. If this is not the case the users can be connected already after one minute. At times when no switching operations are necessary, e.g. during night time, the switching contingent is successively increased again. This ensures that the maximum number of switching operations (time when the components must be replaced) is not reached prematurely.

Switching from the direct line to the public grid is possible at any time to ensure that no more PV-energy is drawn from the direct lines than is actually available.

## Data Set
The example data set contains anonymized measurement data from the pilot in Thannhausen. The data is available for two days and includes 

- the energy consumption of eight consumers and

- the energy production of the photovoltaic system.

All data is measured in Watt with a resolution of 15 seconds.

## Get Started

1. Download the *SoWeit_Connected_Optimierer.py*, the *SoWeiT_Connected_Testfunktion.py* and the testing data set *Testdaten.csv*

2. If necessary install following libraries:

   - numpy

   - pandas

   - datetime

3. Install the [cbc-Solver](https://github.com/coin-or/Cbc) for Python

4. Run the *SoWeiT_Connected_Testfunktion.py*

## License
This project is licensed under the [GNU General Public License 3](https://www.gnu.org/licenses/gpl-3.0)

Copyright (c) 2023 4ward Energy Research GmbH
