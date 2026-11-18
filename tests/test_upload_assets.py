import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('uploader',Path(__file__).resolve().parents[1]/'tools/upload_assets.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class UploadTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)
  (self.p/'INSTALL.md').write_bytes(b'instructions')
  hashes={'INSTALL.md':hashlib.sha256(b'instructions').hexdigest()}
  (self.p/'manifest.json').write_text(json.dumps({'repository':u.REPO,'tag':'v1.3.1','revision':'a'*40,'files':hashes,'source_merge_status':'merged'}))
  hashes={**hashes,'manifest.json':hashlib.sha256((self.p/'manifest.json').read_bytes()).hexdigest()}
  (self.p/'SHA256SUMS').write_text(''.join(f'{h}  {n}\n' for n,h in hashes.items()))
 def test_document_upload_type_and_no_overwrite(self):
  r={'databaseId':12,'isDraft':True,'assets':[],'targetCommitish':'a'*40}
  with patch.object(u.subprocess,'check_output',return_value=json.dumps(r).encode()),patch.object(u.subprocess,'run') as run:
   u.upload(self.p,'v1.3.1')
   cmd=next(c.args[0] for c in run.call_args_list if str(self.p/'INSTALL.md') in c.args[0])
   self.assertIn('Content-Type: text/plain; charset=utf-8',cmd)
  for bad in ({**r,'isDraft':False},{**r,'assets':[{}]},{**r,'targetCommitish':'b'*40}):
   with patch.object(u.subprocess,'check_output',return_value=json.dumps(bad).encode()),patch.object(u.subprocess,'run') as run,self.assertRaises(ValueError):
    u.upload(self.p,'v1.3.1')
   run.assert_not_called()
 def test_corruption_and_extra_files_fail_before_upload(self):
  (self.p/'INSTALL.md').write_bytes(b'corrupt')
  with self.assertRaises(ValueError):u.verify(self.p,'v1.3.1')
  (self.p/'extra.txt').write_text('extra')
  with self.assertRaises(ValueError):u.verify(self.p,'v1.3.1')
 def test_pending_mcp_source_blocks_upload_before_remote_access(self):
  manifest=u.verify(self.p,'v1.3.1')
  pending={**manifest,'source_merge_status':'pending'}
  with patch.object(u,'verify',return_value=pending),patch.object(u.subprocess,'check_output') as remote:
   with self.assertRaisesRegex(ValueError,'MCP source must merge'):
    u.upload(self.p,'v1.3.1')
   remote.assert_not_called()
