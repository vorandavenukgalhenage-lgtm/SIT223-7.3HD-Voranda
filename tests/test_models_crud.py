from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from home.models import Announcement, Contact, Course, Job, Project


class JobCRUDTests(TestCase):
    def make_job(self, **overrides):
        data = {
            'title': 'Backend Developer',
            'description': 'Build and maintain APIs',
            'location': 'Melbourne',
            'job_type': 'Full-time',
            'closing_date': timezone.now() + timedelta(days=30),
        }
        data.update(overrides)
        return Job.objects.create(**data)

    def test_create_job(self):
        job = self.make_job()
        self.assertTrue(Job.objects.filter(pk=job.pk).exists())

    def test_read_job(self):
        self.make_job(title='Readable Job')
        self.assertEqual(Job.objects.get(title='Readable Job').location, 'Melbourne')

    def test_update_job(self):
        job = self.make_job()
        job.location = 'Sydney'
        job.save()
        job.refresh_from_db()
        self.assertEqual(job.location, 'Sydney')

    def test_delete_job(self):
        job = self.make_job()
        pk = job.pk
        job.delete()
        self.assertFalse(Job.objects.filter(pk=pk).exists())


class ProjectCRUDTests(TestCase):
    def test_create_project(self):
        project = Project.objects.create(title='Website Revamp', description='Redesign')
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_read_project(self):
        Project.objects.create(title='Readable Project', description='Desc')
        self.assertEqual(Project.objects.get(title='Readable Project').description, 'Desc')

    def test_update_project(self):
        project = Project.objects.create(title='Old Title')
        project.title = 'New Title'
        project.archived = True
        project.save()
        project.refresh_from_db()
        self.assertEqual(project.title, 'New Title')
        self.assertTrue(project.archived)

    def test_delete_project(self):
        project = Project.objects.create(title='Delete Me')
        pk = project.pk
        project.delete()
        self.assertFalse(Project.objects.filter(pk=pk).exists())


class CourseCRUDTests(TestCase):
    def test_create_course(self):
        course = Course.objects.create(title='Intro to Security', code='SIT900')
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())

    def test_read_course(self):
        Course.objects.create(title='Readable Course', code='SIT901')
        self.assertEqual(Course.objects.get(code='SIT901').title, 'Readable Course')

    def test_update_course(self):
        course = Course.objects.create(title='Old', code='SIT902')
        course.title = 'Updated'
        course.save()
        course.refresh_from_db()
        self.assertEqual(course.title, 'Updated')

    def test_delete_course(self):
        course = Course.objects.create(title='Delete Me', code='SIT903')
        pk = course.pk
        course.delete()
        self.assertFalse(Course.objects.filter(pk=pk).exists())


class ContactCRUDTests(TestCase):
    def make_contact(self, **overrides):
        data = {'name': 'Alex', 'email': 'alex@example.com', 'message': 'Hello team'}
        data.update(overrides)
        return Contact.objects.create(**data)

    def test_create_contact(self):
        contact = self.make_contact()
        self.assertTrue(Contact.objects.filter(pk=contact.pk).exists())

    def test_read_contact(self):
        self.make_contact(name='Readable')
        self.assertEqual(Contact.objects.get(name='Readable').email, 'alex@example.com')

    def test_update_contact(self):
        contact = self.make_contact()
        contact.message = 'Updated message'
        contact.save()
        contact.refresh_from_db()
        self.assertEqual(contact.message, 'Updated message')

    def test_delete_contact(self):
        contact = self.make_contact()
        pk = contact.pk
        contact.delete()
        self.assertFalse(Contact.objects.filter(pk=pk).exists())


class AnnouncementCRUDTests(TestCase):
    def test_create_announcement(self):
        item = Announcement.objects.create(message='Site maintenance tonight')
        self.assertTrue(Announcement.objects.filter(pk=item.pk).exists())

    def test_read_announcement(self):
        Announcement.objects.create(message='Readable notice')
        self.assertEqual(Announcement.objects.filter(message='Readable notice').count(), 1)

    def test_update_announcement(self):
        item = Announcement.objects.create(message='Old notice')
        item.isActive = False
        item.save()
        item.refresh_from_db()
        self.assertFalse(item.isActive)

    def test_delete_announcement(self):
        item = Announcement.objects.create(message='Delete me')
        pk = item.pk
        item.delete()
        self.assertFalse(Announcement.objects.filter(pk=pk).exists())