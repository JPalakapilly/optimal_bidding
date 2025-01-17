import sys
import os
import pandas as pd
import numpy as np

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from optimal_bidding.environments.energy_market import FCASMarket
from optimal_bidding.environments.agents import Battery, Bid
from optimal_bidding.utils.nets import ActorNet, CriticNet
import optimal_bidding.utils.data_postprocess as data_utils


class ActorCritic():
    def __init__(self):
        # hyperparameters
        self._exploration_size = None
        self._actor_step_size = 0.01
        self._critic_step_size = 0.01
        self._discount_factor = 0.95
        self._eligibility_trace_decay_factor = 0.7

        self._fcas_market = FCASMarket()
        self._battery = Battery()
        self._actor_nn = ActorNet()
        self._critic_nn = CriticNet()

        self._eligibility = 0
        self._delta = None

    def run_simulation(self):
        end = False
        index = 0
        k = 1
        while not end:
            timestamp = self._fcas_market.get_timestamp()
            print('timestamp: %s' % timestamp)

            # create the state:
            soe = self._battery.get_soe()
            step_of_day = self._get_step_of_day(timestamp)
            state = np.array([step_of_day, soe, ...])

            # compute the action = [p_raise, c_raise, p_energy]
            action = self._compute_action(state, k, timestamp)
            energy_cleared_price = data_utils.get_energy_price(timestamp)
            fcas_bid, energy_bid = self._transform_to_bid(
                action, energy_cleared_price)

            # run the market dispatch
            fcas_bid_cleared, fcas_clearing_price, end = self._fcas_market.step(
                fcas_bid)

            # update soe of the battery with the cleared power
            self._battery.step(fcas_bid_cleared.power_signed(),
                               energy_bid.power_signed())

            reward = self._compute_reward(bid_fcas, bid_energy,
                                          energy_cleared_price,
                                          fcas_bid_cleared)

            # run backpropagation
            self._critic_nn(state).backward()
            action.backward()

            self._delta = r + self._discount_factor * self._critic_nn(
                next_state) - self._critic_nn(state)

            # update neural nets
            self._update_critic()
            self._update_actor()

            index += 1

    def _update_critic(self):
        self._critic_nn.fc1.data += - self._delta * self._critic_step_size * elf._discount_factor * self._eligibility * self._eligibility_trace_decay_factor + self._critic_nn.fc1.grad.data
        self._critic_nn.fc2.data += - self._delta * self._critic_step_size * elf._discount_factor * self._eligibility * self._eligibility_trace_decay_factor + self._critic_nn.fc2.grad.data
        self._critic_nn.fc3.data += - self._delta * self._critic_step_size * elf._discount_factor * self._eligibility * self._eligibility_trace_decay_factor + self._critic_nn.fc3.grad.data

        self._critic_nn.data.zero_()

    def _transform_to_bid(self, action, energy_cleared_price):
        bid_fcas = Bid(action[0], action[1], bid_type='gen')
        if action[2] >= 0:
            bid_energy = Bid(action[2], energy_cleared_price, bid_type='load')
        else:
            bid_energy = Bid(action[2], energy_cleared_price, bid_type='gen')
        return bid_fcas, bid_energy

    def _get_action_actor(self, state):
        action = self._actor_nn(state)
        return action

    def _compute_action(self, state, timestamp, k):
        bid_fcas_mpc, bid_energy_mpc = self._battery.bid_mpc(timestamp)
        action_supervisor = np.array([
            bid_fcas_mpc.power_signed(),
            bid_fcas_mpc.price(),
            bid_energy_mpc.power_signed()
        ])
        action_actor = self._get_action_actor(state)
        return k * action_supervisor + (1 - k) * action_actor

    def _compute_reward(self, bid_fcas, bid_energy, energy_cleared_price,
                        fcas_bid_cleared):
        # assume the markets are pay-as-bid
        # assume the energy market always clears your bid
        energy_cleared_power = bid_energy.power_signed()
        # energy_bid_price = bid_energy.price()

        fcas_cleared_price = bid_fcas.price()
        fcas_bid_power = bid_fcas.power_signed()
        fcas_cleared_power = fcas_bid_cleared.power_signed()

        # bare bones reward function
        reward = - energy_cleared_power * energy_cleared_price +\
                0.9 * fcas_cleared_power * fcas_cleared_price

        soe = self._battery.get_soe()
        total_capacity = self._battery._total_capacity
        max_power = self._battery._max_power
        max_ramp = self._battery._max_ramp

        new_energy = soe + self._battery._efficiency * energy_cleared_power +\
                self._battery._ratio_fcast * fcas_cleared_power

        # weight the constraints by how 'much' the constraint
        # is violated multiplied by some scalar. this can be changed.
        # only punish if bounds on capacity, power, or ramp are violated.
        penalty = 50

        if new_energy > total_capacity:
            reward -= penalty * (new_energy - total_capacity)
        if new_energy < 0:
            reward -= penalty * (-new_energy)
        if -fcas_bid_power > max_ramp:
            reward -= penalty * fcas_bid_power

        # penalize "low" fcas bids
        if fcas_bid_power > 0:
            reward -= penalty * fcas_bid_power
        if -fcas_bid_power > max_ramp:
            reward -= penalty * (-fcas_bid_power - max_ramp)
        if -energy_cleared_power > max_power:
            reward -= penalty * (-energy_cleared_power - max_power)

        return reward


def save_data(battery_bid_fcas, battery_bid_energy, fcas_cleared_power,
              fcas_clearing_price, soe, index, timestamp, energy_price,
              low_price, raise_price):
    """This function is just to save the data in a csv. To be changed as needed!
    """
    d = {}
    d['battery_bid_fcas_power'] = battery_bid_fcas.power()
    d['battery_bid_fcas_price'] = battery_bid_fcas.price()
    d['battery_bid_fcas_type'] = battery_bid_fcas.type()

    if battery_bid_energy.type() == 'gen':
        d['battery_bid_energy_power_gen'] = battery_bid_energy.power_signed()
        d['battery_bid_energy_power_load'] = 0
    else:
        d['battery_bid_energy_power_gen'] = 0
        d['battery_bid_energy_power_load'] = battery_bid_energy.power_signed()

    d['battery_bid_energy_price'] = battery_bid_energy.price()
    d['battery_bid_energy_type'] = battery_bid_energy.type()

    d['fcas_clearing_price'] = fcas_clearing_price
    d['energy_price'] = energy_price
    d['low_price'] = low_price
    d['raise_price'] = raise_price
    d['soe'] = soe
    d['timestamp'] = timestamp

    df = pd.DataFrame(data=d, index=[index])
    with open('mpc_results.csv', 'a') as f:
        if index == 0:
            df.to_csv(f, header=True)
        else:
            df.to_csv(f, header=False)


def main():
    actor_critic = ActorCritic()
    actor_critic.run_simulation()


if __name__ == '__main__':
    main()
