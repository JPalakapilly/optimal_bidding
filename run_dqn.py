import tensorflow as tf

import agent.dqn as dqn
from agent.dqn_utils import *
from energy_market_model.energy_market_model import Env


def model(input, num_actions, scope, reuse=False):
    with tf.variable_scope(scope, reuse=reuse):
        out = input
        with tf.variable_scope("action_value"):
            out = tf.contrib.layers.fully_connected(out, num_outputs=32,         activation_fn=tf.nn.relu)
            out = tf.contrib.layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)

        return out


def learn(env,
          session,
          num_timesteps):
    # This is just a rough estimate
    num_iterations = float(num_timesteps) / 4.0

    lr_multiplier = 1.0
    lr_schedule = PiecewiseSchedule([
                                         (0,                   1e-4 * lr_multiplier),
                                         (num_iterations / 10, 1e-4 * lr_multiplier),
                                         (num_iterations / 2,  5e-5 * lr_multiplier),
                                    ],
                                    outside_value=5e-5 * lr_multiplier)
    optimizer = dqn.OptimizerSpec(
        constructor=tf.train.AdamOptimizer,
        kwargs=dict(epsilon=1e-4),
        lr_schedule=lr_schedule
    )

    def stopping_criterion(env, t):
        # notice that here t is the number of steps of the wrapped env,
        # which is different from the number of steps in the underlying env
        return t > 1000000

    exploration_schedule = PiecewiseSchedule(
        [
            (0, 1.0),
            (5e5, 0.0),
            (num_iterations / 2, 0.01),
        ], outside_value=0.01
    )

    dqn.learn(
        env=env,
        q_func=model,
        optimizer_spec=optimizer,
        session=session,
        exploration=exploration_schedule,
        stopping_criterion=stopping_criterion,
        replay_buffer_size=1000000,
        batch_size=32,
        gamma=0.99,
        learning_starts=50000,
        learning_freq=4,
        frame_history_len=4,
        target_update_freq=10000,
        grad_norm_clipping=10,
        double_q=True,
    )
    env.close()


def get_available_gpus():
    from tensorflow.python.client import device_lib
    local_device_protos = device_lib.list_local_devices()
    return [x.physical_device_desc for x in local_device_protos if x.device_type == 'GPU']


def get_session():
    tf.reset_default_graph()
    tf_config = tf.ConfigProto(
        inter_op_parallelism_threads=1,
        intra_op_parallelism_threads=1)
    session = tf.Session(config=tf_config)
    print("AVAILABLE GPUS: ", get_available_gpus())
    return session


def main():
    env = Env(num_other_agents=1)
    session = get_session()
    learn(env, session, num_timesteps=2e8)


if __name__ == "__main__":
    main()