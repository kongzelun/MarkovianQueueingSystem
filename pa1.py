#!/usr/bin/env python

#
# Zelun Kong
# zxk170230
#

from math import log


class Uniform:
    def __init__(self):
        self.seed = 1234
        self.k = 16807
        self.m = 2147483647

    def __call__(self):
        self.seed = (self.k * self.seed) % self.m
        return self.seed / self.m


class Exponential:
    def __init__(self, mu):
        self.mu = mu
        self.uniform = Uniform()

    def __call__(self):
        return - 1 / self.mu * log(self.uniform())


class Event:
    """
    Event base class. 
    """

    def __init__(self, t, time, customer):
        self._t = t
        self._time = time
        self._customer = customer

        if self.t not in {'a', 'd'}:
            raise ValueError("Unknown event type.")

    @property
    def t(self):
        return self._t

    @property
    def time(self):
        return self._time

    @property
    def customer(self):
        return self._customer

    def __repr__(self):
        return f"{self.t}({self.customer:6d}): {self.time:.3f} "


class MarkovianQueueingSystem:
    """
    Markovian Queueing System
    """

    def __init__(self, K, mu):
        self.m = 2
        self.K = K
        self.mu = mu
        self.current_time = 0.0
        self.queue = []
        self._used_server = 0

        self._uniform = Uniform()
        self._service_interval = Exponential(mu=self.mu)

        self.total_operation_time = 0.0
        self.blocked_number = 0
        self.total_time = 0.0
        self.expected_number = 0.0
        self.number_time_product_sum = 0.0

        if self.K < 2:
            raise ValueError("K >= 2")

    @property
    def customer_number(self):
        return len(self.queue) + self._used_server

    @property
    def usable_server(self):
        if self.customer_number < self.K:
            return 1
        elif self.customer_number <= 2*self.K:
            return self.m

    @property
    def idle_server(self):
        idle_server = self.usable_server - self._used_server
        assert 0 <= idle_server <= self.usable_server
        return idle_server

    def process_event(self, e: Event):
        """
        `return`: whether new customer entering service
        """
        previous_time = self.current_time
        self.current_time = e.time
        self.number_time_product_sum += self.customer_number * (self.current_time - previous_time)

        if e.t == 'a':
            if self.customer_number < self.K:
                self.queue.append(e)
            elif self.customer_number < 2*self.K and self._uniform() >= 0.5:
                self.queue.append(e)
            else:
                self.blocked_number += 1
                raise Exception("The customer is blocked.")
        elif e.t == 'd':
            self._used_server -= 1

        if self.customer_number > 0 and self.idle_server > 0:
            arrival_event = self.queue.pop(0)
            operation_time = self._service_interval()
            self.total_operation_time += operation_time
            self.total_time = self.current_time - arrival_event.time + operation_time
            self._used_server += 1
            return Event('d', time=self.current_time + operation_time, customer=arrival_event.customer)


class Simulator:
    def __init__(self, mqs: MarkovianQueueingSystem, lambda_, times=100000):
        self.mqs = mqs
        self._lambda_ = lambda_
        self._times = times
        self._event_list = []
        self._arrival_interval = Exponential(mu=self._lambda_)

    @property
    def times(self):
        return self._times

    def _append_event(self, e):
        self._event_list.append(e)
        self._event_list.sort(key=lambda e: e.time)

    def __call__(self):
        total_number = 0
        total_operating_time = 0.0
        departure_event_number = 0

        # Generate first arrival event
        total_number += 1
        self._append_event(Event('a', self._arrival_interval(), customer=total_number))

        while departure_event_number < self._times:
            event = self._event_list.pop(0)

            if event.t == 'd':
                departure_event_number += 1
                print(f"{event} [{departure_event_number}]")
            else:
                print(event)

            try:
                departure_event = self.mqs.process_event(event)
            except Exception as e:
                print(event, e)
            else:
                if departure_event:
                    self._append_event(departure_event)
            finally:
                if event.t == 'a':
                    total_number += 1
                    self._append_event(Event('a', self.mqs.current_time + self._arrival_interval(), total_number))

        # print(f"Total: {total_number} Blocked: {self.mqs.blocked_number} Average Time: {self.mqs.total_time/total_number:.3f} Utilization: {0}")


if __name__ == "__main__":
    average_number = []
    average_time = []
    block_probability = []
    total_utilization = []

    for rho in range(10):
        MQS = MarkovianQueueingSystem(K=4, mu=3)
        SIMULATOR = Simulator(MQS, lambda_=(rho+1)/10 * MQS.m * MQS.mu)

        SIMULATOR()

        average_number.append(MQS.number_time_product_sum / MQS.current_time)
        average_time.append(MQS.total_time / SIMULATOR.times)
        block_probability.append(MQS.blocked_number / SIMULATOR.times)
        total_utilization.append(MQS.total_operation_time / (MQS.current_time * MQS.m))

    print(average_number)
    print(average_time)
    print(block_probability)
    print(total_utilization)


