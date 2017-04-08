# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

"""
Unit tests for the sequnce_softmax.
"""

import numpy as np
import pytest
import cntk as C
from .. import *
from cntk.losses import *
from ...axis import Axis
from ... import sequence, input
from .ops_test_utils import cntk_device
from cntk.tests.test_utils import _to_dense, _to_csr

def test_sequnce_max():
  np.random.seed(0)
  a = np.float32(np.random.rand(20,100,1))
  src = sequence.input(shape=(1), sequence_axis=Axis("Seq"))
  out = sequence.reduce_max(src)
  val = out.eval({src:a})
  expected = np.max(a, 1) 
  assert np.allclose(val, expected)

def np_softmax(a):
  m = np.reshape(np.repeat(np.max(a, 1), a.shape[1], 1), a.shape)
  e = np.exp((a-m)*10)
  s = np.reshape(np.repeat(np.sum(e, 1), a.shape[1], 1), a.shape)
  return e/s
  
def test_sequnce_softmax():
  np.random.seed(0)
  a = np.float32(np.random.rand(20,100,1))
  src = sequence.input(shape=(1), sequence_axis=Axis("Seq"))
  out = sequence.softmax(src)
  val = out.eval({src:a})
  expected = np_softmax(a)
  assert np.allclose(val, expected)


def test_to_sequence(device_id):
    dev = cntk_device(device_id)
    x = C.input((C.FreeDimension, 2))
    x_seq = C.to_sequence(x)
    assert len(x_seq.dynamic_axes) == 2

    x_data = np.asarray([[[1, 2], [-1000, -1000]], [[3, 4], [5, 6]]], dtype=np.float32)
    result = x_seq.eval({x : x_data}, device=dev)
    assert np.array_equal(result, x_data)

    x = C.input((C.FreeDimension, 2, 3), is_sparse=True)
    x_seq_lens = C.input(())
    x_seq = C.to_sequence(x, x_seq_lens)
    
    seq1_data = [[[0, 1, 1], [0, 1, 0]], [[1, 0, 0], [1, 0, 1]]]
    csr_seq1 = _to_csr(seq1_data)
    ndarrayview1 = C.NDArrayView.from_csr(csr_seq1, shape=(2, 2, 3), device=C.cpu())
    seq2_data = [[0, 1, 1], [1, 1, 0]]
    csr_seq2 = _to_csr([seq2_data, [[0, 0, 0], [0, 0, 0]]])
    ndarrayview2 = C.NDArrayView.from_csr(csr_seq2, shape=(2, 2, 3), device=C.cpu())

    x_data = C.Value.create(C.input((2, 2, 3), is_sparse=True), [ndarrayview1, ndarrayview2], device=dev).data
    x_seq_lens_data = np.asarray([2, 1], dtype=np.float32)
    result = x_seq.eval({x : x_data, x_seq_lens : x_seq_lens_data}, device=dev, as_numpy=False)
    result_dense = _to_dense(result, True)
    assert np.array_equal(result_dense[0], seq1_data)
    assert np.array_equal(result_dense[1], [seq2_data])
