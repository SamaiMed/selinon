#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ####################################################################
# Copyright (C) 2016  Fridolin Pokorny, fpokorny@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################

from selinonTestCase import SelinonTestCase

from selinon import SystemState


# Let's make it constant, this shouldn't affect tests at all
_FOREACH_COUNT = 20


class TestForeach(SelinonTestCase):
    def test_foreach_start(self):
        #
        # flow1:
        #
        #       |      |             |
        #     Task1  Task1   ...   Task1
        #
        # Note:
        #   There will be spawned _FOREACH_COUNT Task2
        #
        edge_table = {
            'flow1': [{'from': [], 'to': ['Task1'], 'condition': self.cond_true,
                       'foreach': lambda x, y: range(_FOREACH_COUNT), 'foreach_propagate_result': False}]
        }
        self.init(edge_table)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        self.assertIsNotNone(retry)
        self.assertIsNone(system_state.node_args)
        self.assertIn('Task1', self.instantiated_tasks)
        self.assertEqual(len(self.get_all_tasks('Task1')), _FOREACH_COUNT)
        tasks_state_dict = [node for node in state_dict['active_nodes'] if node['name'] == 'Task1']
        self.assertEqual(len(tasks_state_dict), _FOREACH_COUNT)

    def test_foreach_basic(self):
        #
        # flow1:
        #
        #             Task1
        #               |
        #               |
        #       ---------------------
        #       |      |             |
        #       |      |             |
        #     Task2  Task2   ...   Task2
        #
        # Note:
        #   There will be spawned _FOREACH_COUNT Task2
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true,
                       'foreach': lambda x, y: range(_FOREACH_COUNT), 'foreach_propagate_result': False},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true}]
        }
        self.init(edge_table)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        self.assertIsNotNone(retry)
        self.assertIsNone(system_state.node_args)
        self.assertIn('Task1', self.instantiated_tasks)
        self.assertNotIn('Task2', self.instantiated_tasks)

        # Task1 has finished
        task1 = self.get_task('Task1')
        self.set_finished(task1, "some result")

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        self.assertIsNotNone(retry)
        self.assertIsNone(system_state.node_args)
        self.assertIn('Task1', self.instantiated_tasks)
        self.assertIn('Task2', self.instantiated_tasks)

        self.assertEqual(len(self.get_all_tasks('Task2')), _FOREACH_COUNT)
        tasks_state_dict = [node for node in state_dict['active_nodes'] if node['name'] == 'Task2']
        self.assertEqual(len(tasks_state_dict), _FOREACH_COUNT)

    def test_foreach_propagate_result(self):
        #
        # flow1:
        #
        #             Task1
        #               |
        #               |
        #       ---------------------
        #       |      |             |
        #       |      |             |
        #     flow2  flow2   ...   flow2
        #
        # Note:
        #   There will be spawned _FOREACH_COUNT flow2, arguments are passed from foreach function
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['flow2'], 'condition': self.cond_true,
                       'foreach': lambda x, y: range(_FOREACH_COUNT), 'foreach_propagate_result': True},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true}],
            'flow2': []
        }
        self.init(edge_table)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        self.assertIsNotNone(retry)
        self.assertIsNone(system_state.node_args)
        self.assertIn('Task1', self.instantiated_tasks)
        self.assertNotIn('Task2', self.instantiated_tasks)

        # Task1 has finished
        task1 = self.get_task('Task1')
        self.set_finished(task1, "some result")

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        self.assertIsNotNone(retry)
        self.assertIsNone(system_state.node_args)
        self.assertIn('Task1', self.instantiated_tasks)
        self.assertIn('flow2', self.instantiated_flows)

        tasks_state_dict = [node for node in state_dict['active_nodes'] if node['name'] == 'flow2']
        self.assertEqual(len(tasks_state_dict), _FOREACH_COUNT)

        # Inspect node_args as we set propagate_result for foreach
        all_flow_args = [flow.node_args for flow in self.get_all_flows('flow2')]
        self.assertEqual(all_flow_args, list(range(_FOREACH_COUNT)))
