
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from turbogears.database import session
from bkr.inttest import with_transaction, data_setup
from bkr.inttest.client import run_client, create_client_config, ClientError, \
        ClientTestCase
from bkr.server.model import TaskBase

class JobModifyTest(ClientTestCase):

    @with_transaction
    def setUp(self):
        user = data_setup.create_user(password='password')
        self.job = data_setup.create_job(owner=user)
        self.job_for_rs = data_setup.create_job(owner=user)
        self.client_config = create_client_config(username=user.user_name,
                                                  password='password')

    def test_retention_tag_product(self):
        with session.begin():
            rt1 = data_setup.create_retention_tag()
            rt2 = data_setup.create_retention_tag(needs_product=True)
            p1 = data_setup.create_product()
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--retention-tag', '%s' % rt1.tag])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.t_id)
        session.expunge_all()
        j = TaskBase.get_by_t_id(self.job.t_id)
        self.assert_(j.retention_tag.tag == rt1.tag)
        out = run_client(['bkr', 'job-modify', self.job.t_id, '--retention-tag', '%s' % rt2.tag, '--product', '%s' % p1.name])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.t_id)
        session.expunge_all()
        j = TaskBase.get_by_t_id(self.job.t_id)
        self.assert_(j.retention_tag.tag == rt2.tag)
        self.assert_(j.product.name == p1.name)
        out = run_client(['bkr', 'job-modify', self.job.t_id, '--retention-tag', '%s' % rt1.tag, '--product='])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.t_id)
        session.expunge_all()
        j = TaskBase.get_by_t_id(self.job.t_id)
        self.assert_(j.retention_tag.tag == rt1.tag)
        self.assert_(j.product is None)

    # https://bugzilla.redhat.com/show_bug.cgi?id=877344
    def test_empty_product_name_is_always_accepted(self):
        with session.begin():
            job = data_setup.create_job(retention_tag=u'scratch')
        out = run_client(['bkr', 'job-modify', job.t_id,
                '--retention-tag', '60days', '--product', ''])
        self.assertIn('Successfully modified', out)

    def test_ack_already_acked_job(self):
        # Is this lazy?
        self.test_ack_job()
        self.test_ack_job()

    def test_ack_job(self):
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--response', 'ack'])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.t_id)
        j = TaskBase.get_by_t_id(self.job.t_id)
        for rs in j.recipesets:
            self.assert_('%s' % rs.nacked.response == 'ack')

    def test_nak_job(self):
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--response', 'nak'])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.t_id)
        j = TaskBase.get_by_t_id(self.job.t_id)
        for rs in j.recipesets:
            self.assert_('%s' % rs.nacked.response == 'nak')

    def test_multiple_response_job(self):
        out = run_client(['bkr', 'job-modify', self.job.t_id, self.job_for_rs.t_id,  '--response', 'ack'])

        self.assert_('Successfully modified jobs' in out and
                     self.job.t_id in out and
                     self.job_for_rs.t_id in out)
        j = TaskBase.get_by_t_id(self.job.t_id)
        for rs in j.recipesets:
            self.assert_('%s' % rs.nacked.response == 'ack')
        j2 = TaskBase.get_by_t_id(self.job_for_rs.t_id)
        for rs in j2.recipesets:
            self.assert_('%s' % rs.nacked.response == 'ack')

    def test_ack_rs(self):
        out = run_client(['bkr', 'job-modify', self.job.recipesets[0].t_id,  '--response', 'ack'])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.recipesets[0].t_id)
        rs = TaskBase.get_by_t_id(self.job.recipesets[0].t_id)
        self.assert_('%s' % rs.nacked.response == 'ack')

    def test_nak_rs(self):
        out = run_client(['bkr', 'job-modify', self.job.recipesets[0].t_id,  '--response', 'nak'])
        self.assert_(out == 'Successfully modified jobs %s\n' % self.job.recipesets[0].t_id)
        rs = TaskBase.get_by_t_id(self.job.recipesets[0].t_id)
        self.assert_('%s' % rs.nacked.response == 'nak')

    def test_multiple_response_recipeset(self):
        out = run_client(['bkr', 'job-modify', self.job.recipesets[0].t_id,
                          self.job_for_rs.recipesets[0].t_id,  '--response', 'ack'])
        self.assert_('Successfully modified jobs' in out and \
                     self.job_for_rs.recipesets[0].t_id in out and \
                     self.job.recipesets[0].t_id in out,)
        rs = TaskBase.get_by_t_id(self.job.recipesets[0].t_id)
        self.assert_('%s' % rs.nacked.response == 'ack')
        rs = TaskBase.get_by_t_id(self.job_for_rs.recipesets[0].t_id)
        self.assert_('%s' % rs.nacked.response == 'ack')

    # https://bugzilla.redhat.com/show_bug.cgi?id=595512
    def test_invalid_taskspec(self):
        try:
            run_client(['bkr', 'job-modify', '12345', '--response', 'ack'])
            fail('should raise')
        except ClientError, e:
            self.assert_('Invalid taskspec' in e.stderr_output)

    # https://bugzilla.redhat.com/show_bug.cgi?id=995012
    def test_record_retention_tag(self):
        with session.begin():
            rt = data_setup.create_retention_tag()
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--retention-tag', '%s' % rt.tag])
        self.assertEquals(self.job.activity[0].action, u'Changed')
        self.assertEquals(self.job.activity[0].field_name, 'Retention Tag')
        self.assertEquals(self.job.activity[0].old_value, self.job.retention_tag.tag)
        self.assertEquals(self.job.activity[0].new_value, rt.tag)

    # https://bugzilla.redhat.com/show_bug.cgi?id=995012
    def test_record_ack_job(self):
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--response', 'ack'])
        self.assertEquals(self.job.recipesets[0].activity[0].action, u'Changed')
        self.assertEquals(self.job.recipesets[0].activity[0].field_name, 'Ack/Nak')
        self.assertEquals(self.job.recipesets[0].activity[0].new_value, 'ack')

    # https://bugzilla.redhat.com/show_bug.cgi?id=995012
    def test_record_ack_rs(self):
        out = run_client(['bkr', 'job-modify', self.job.recipesets[0].t_id,  '--response', 'ack'])
        self.assertEquals(self.job.recipesets[0].activity[0].action, u'Changed')
        self.assertEquals(self.job.recipesets[0].activity[0].field_name, 'Ack/Nak')
        self.assertEquals(self.job.recipesets[0].activity[0].new_value, 'ack')

    # https://bugzilla.redhat.com/show_bug.cgi?id=1149977
    def test_increase_priority(self):
        out = run_client(['bkr', 'job-modify', self.job.t_id,  '--priority', 'High'])
        self.assertIn('Successfully modified jobs %s' % self.job.t_id, out)
        with session.begin():
            session.expire_all()
            for rs in self.job.recipesets:
                self.assertEquals(rs.priority.value, 'High')
            self.assertEquals(self.job.recipesets[0].activity[0].action, u'Changed')
            self.assertEquals(self.job.recipesets[0].activity[0].field_name, 'Priority')
            self.assertEquals(self.job.recipesets[0].activity[0].new_value, 'High')
