#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:mod:`test_client`
==================

.. module:: test_client
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: hbldh <henrik.blidh@nedomkull.com>

Created on 2015-08-07, 12:00

"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import random
import tempfile
import uuid

import pytest

import bankid


def _get_random_personal_number():
    """Simple random Swedish personal number generator."""

    def _luhn_digit(id_):
        """Calculate Luhn control digit for personal number.

        Code adapted from [Faker]
        (https://github.com/joke2k/faker/blob/master/faker/providers/ssn/sv_SE/__init__.py)

        :param id_: The partial number to calculate checksum of.
        :type id_: str
        :return: Integer digit in [0, 9].
        :rtype: int

        """

        def digits_of(n):
            return [int(i) for i in str(n)]
        id_ = int(id_) * 10
        digits = digits_of(id_)
        checksum = sum(digits[-1::-2])
        for k in digits[-2::-2]:
            checksum += sum(digits_of(k * 2))
        checksum %= 10

        return checksum if checksum == 0 else 10 - checksum

    year = random.randint(1900, 2014)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    suffix = random.randint(0, 999)
    pn = "{0:04d}{1:02d}{2:02d}{3:03d}".format(year, month, day, suffix)
    return pn + str(_luhn_digit(pn[2:]))



@pytest.fixture(scope="module")
def get_test_cert_and_key():
    return bankid.create_bankid_test_server_cert_and_key(tempfile.gettempdir())


def test_authentication_and_collect():
    """Authenticate call and then collect with the returned orderRef UUID."""

    c = bankid.BankIDClient(certificates=get_test_cert_and_key(), test_server=True)
    out = c.authenticate(_get_random_personal_number())
    assert isinstance(out, dict)
    # UUID.__init__ performs the UUID compliance assertion.
    order_ref = uuid.UUID(out.get('orderRef'), version=4)
    collect_status = c.collect(out.get('orderRef'))
    assert collect_status.get('progressStatus') in ('OUTSTANDING_TRANSACTION', 'NO_CLIENT')


@pytest.mark.xfail(raises=bankid.exceptions.InvalidParametersError)
def test_invalid_orderref_raises_error():
    c = bankid.BankIDClient(certificates=get_test_cert_and_key(), test_server=True)
    collect_status = c.collect('invalid-uuid')


@pytest.mark.xfail(raises=bankid.exceptions.AlreadyInProgressError)
def test_already_in_progress_raises_error():
    c = bankid.client.BankIDClient(certificates=get_test_cert_and_key(), test_server=True)
    pn = _get_random_personal_number()
    out = c.authenticate(pn)
    out2 = c.authenticate(pn)
