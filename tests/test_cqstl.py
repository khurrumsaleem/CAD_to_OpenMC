# SPDX-FileCopyrightText: 2025 E. B. Knudsen <erik@united-neux.eu>
#
# SPDX-License-Identifier: MIT

import pytest
import CAD_to_OpenMC.assembly as ab
from tests.harnessRun import HarnessRun
import pathlib as pl

class HarnessCqSTL(HarnessRun):
  def run(self,merge=False):

    self.a.import_stp_files()
    if merge:
      self.merge()

    #self.a.solids_to_h5m(backend='stl')
    h5p = pl.Path('out_cqstl.h5m')
    self.a.solids_to_h5m(backend='stl',h5m_filename=str(h5p))
    assert h5p.exists()
    assert self.is_validh5m(h5p)
    self.cleanup()

  def cleanup(self):
    super().cleanup()
    pwd=pl.Path('.')
    for v in pwd.glob("vol*_face*"):
      v.unlink()

def testcq():
  t = HarnessCqSTL()
  t.run()

def testcq_wmerge():
  t = HarnessCqSTL()
  t.run(merge=True)
