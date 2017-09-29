# -*- coding: utf-8 -*-

class Tracer(object):

    def start(self, variable_name, period):
        print("Starting to compute '{}' for period '{}'".format(variable_name, period).encode('utf-8'))

    def stop(self, variable_name, period, result):
        print("Finished computing '{}' for period '{}'. Result: '{}'".format(variable_name, period, result).encode('utf-8'))
