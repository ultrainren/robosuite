#!/usr/bin/env python3
'''
Displays robot fetch at a disco party.
'''

from mujoco_py import load_model_from_path, MjSim, MjViewer
from mujoco_py.generated import const
import numpy as np
import os
import sys
import time

class SaywerPushEnv(object):
    def __init__(self):
        self.model = load_model_from_path('robots/sawyer/arena_2.xml')
        self._get_reference()
        self.sim = MjSim(self.model)
        self.viewer = MjViewer(self.sim)
        self.sim_state_initial = self.sim.get_state()
        self.set_cam()
        self.done = False

    def _get_reference(self):
        self._ref_object_pos_low, self._ref_object_pos_high = self.model.get_joint_qpos_addr('object_free_joint')
        self._ref_object_vel_low, self._ref_object_vel_high = self.model.get_joint_qvel_addr('object_free_joint')
        self._ref_target_x = self.model.get_joint_qpos_addr('target_x')
        self._ref_target_y = self.model.get_joint_qpos_addr('target_y')
        # self._ref_target_z = self.model.get_joint_qpos_addr('target_z')
        self._ref_joint_pos_indexes = [self.model.get_joint_qpos_addr('right_j{}'.format(x)) for x in range(7)]
        self._ref_joint_vel_indexes = [self.model.get_joint_qvel_addr('right_j{}'.format(x)) for x in range(7)]


    def set_cam(self):
        self.viewer.cam.fixedcamid = 0
        # viewer.cam.type = const.CAMERA_FIXED
        self.viewer.cam.azimuth = 179.7749999999999
        self.viewer.cam.distance = 3.825077470729921
        self.viewer.cam.elevation = -21.824999999999992
        self.viewer.cam.lookat[:][0] = 0.09691817
        self.viewer.cam.lookat[:][1] = 0.00164106
        self.viewer.cam.lookat[:][2] = -0.30996464

    def _reset(self):
        self.sim.set_state(self.sim_state_initial)
        self._reset_target()
        self.done = False
        return self._get_observation()

    def _reset_target(self):
        self._target_x = np.random.uniform(high=0.3, low=-0.3)
        self._target_x += self._target_x / abs(self._target_x) * 0.1
        self._target_y = np.random.uniform(high=0.3, low=-0.3)
        self._target_y += self._target_y / abs(self._target_y) * 0.1

    def _step(self, action):
        reward = 0
        info = None
        if not self.done:
            self.sim.data.ctrl[:] = action
            self.sim.step()
            observation = self._get_observation()
            if self._check_win():
                self.done = True
                reward += 10
            elif self._check_lose():
                self.done = True
                reward -= 10
            # TODO: set action penalty coefficient
            reward -= 0.01 * np.linalg.norm(action, 2)
            # if blahblahblah self.done = True
            return observation, reward, self.done, info
        else:
            return self._get_observation(), 0, True, None

    def _get_observation(self):
        # import pdb; pdb.set_trace()
        joint_pos = [self.sim.data.qpos[x] for x in self._ref_joint_pos_indexes]
        joint_pos_sin = np.sin(joint_pos)
        joint_pos_cos = np.cos(joint_pos)
        joint_vel = [self.sim.data.qvel[x] for x in self._ref_joint_vel_indexes]

        hand_pos = self._right_hand_pos
        object_pos = self._object_pos
        target_pos = self._target_pos

        hand_vel = self._right_hand_vel
        object_vel = self._object_vel
        target_vel = self._target_vel

        object_pos_rel = object_pos - hand_pos
        target_pos_rel = target_pos - hand_pos

        object_vel_rel = object_vel - hand_vel
        target_vel_rel = target_vel - hand_vel

        return np.concatenate([joint_pos_sin, 
                                joint_pos_cos, 
                                joint_vel, 
                                object_pos_rel,
                                object_vel_rel,
                                target_pos_rel,
                                target_vel_rel,
                                ])

    def _render(self):
        self.viewer.render()

    def _check_lose(self):
        return False
        return abs(self._object_x) > 0.3 or abs(self._object_y) > 0.3

    def _check_win(self):
        return False
        return np.linalg.norm([self._object_x - self._target_x, self._object_y - self._target_y], 2) < 0.05


    ####
    # Properties for objects
    ####

    @property
    def _object_x(self):
        """
            x-offset of object
        """
        return self.sim.data.qpos[self._ref_object_pos_low] - 0.5

    @_object_x.setter
    def _object_x(self, value):
        self.sim.data.qpos[self._ref_object_pos_low] = 0.5 + value

    @property
    def _object_y(self):
        """
            y-offset of object
        """
        return self.sim.data.qpos[self._ref_object_pos_low + 1]

    @_object_y.setter
    def _object_y(self, value):
        self.sim.data.qpos[self._ref_object_pos_low + 1] = value


    @property
    def _target_x(self):
        """
            x-offset of target
        """
        return self.sim.data.qpos[self._ref_target_x]

    @_target_x.setter
    def _target_x(self, value):
        self.sim.data.qpos[self._ref_target_x] = value

    @property
    def _target_y(self):
        """
            x-offset of target
        """
        return self.sim.data.qpos[self._ref_target_y]

    @_target_y.setter
    def _target_y(self, value):
        self.sim.data.qpos[self._ref_target_y] = value


    @property
    def _right_hand_pos(self):
        return self.sim.data.get_body_xpos('right_hand')

    @property
    def _object_pos(self):
        return self.sim.data.get_body_xpos('object')

    @property
    def _target_pos(self):
        return self.sim.data.get_body_xpos('target')

    @property
    def _right_hand_vel(self):
        return self.sim.data.get_body_xvelp('right_hand')

    @property
    def _object_vel(self):
        return self.sim.data.get_body_xvelp('object')

    @property
    def _target_vel(self):
        return self.sim.data.get_body_xvelp('target')
    
env = SaywerPushEnv()
obs = env._reset()
print('Initial Obs: {}'.format(obs))
while True:
    obs = env._reset()
    # print(obs)
    action = np.random.rand(7) * 2
    for i in range(2000):
        if i % 500 == 499:
            action = np.random.rand(7) * 2 - 1
        obs, reward, done, info = env._step(action)
        # 
        # obs, reward, done, info = env._step([0,-1,0,0,0,0,2])
        # print(obs, reward, done, info)
        env._render()
        if done:
            print('done: {}'.format(reward))
            break
