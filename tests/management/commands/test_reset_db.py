# -*- coding: utf-8 -*-
import os

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings
from six import StringIO

try:
    from unittest.mock import MagicMock, Mock, call, patch
except ImportError:
    from mock import MagicMock, Mock, call, patch


class ResetDbExceptionsTests(TestCase):
    """Tests if reset_db command raises exceptions."""

    def test_should_raise_CommandError_when_router_does_not_exist(self):
        with self.assertRaisesRegexp(
                CommandError, 'Unknown database router non-existing_router'):
            call_command('reset_db', '--router=non-existing_router')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.UNKNOWN',
            'NAME': 'test.db'
        }
    })
    def test_should_raise_CommandError_when_unknown_database_engine(self):
        with self.assertRaisesRegexp(
                CommandError, 'Unknown database engine UNKNOWN'):
            call_command('reset_db', '--noinput')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    })
    def test_should_raise_CommandError_when_no_db_name_provided(self):
        with self.assertRaisesRegexp(
                CommandError, 'You need to specify DATABASE_NAME in your Django settings file.'):  # noqa
            call_command('reset_db', '--noinput')


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_db.sqlite3'
    }
})
class ResetDbSqlite3Tests(TestCase):
    """Tests for reset_db command and sqlite3 engine."""

    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.reset_db.input')
    def test_should_cancel_reset_db_if_input_is_different_than_yes(self, m_input, m_stdout):  # noqa
        m_input.return_value = 'no'
        call_command('reset_db')
        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch.object(os, 'unlink')
    def test_should_unlink_database_and_print_success_message(self, m_unlink, m_stdout):  # noqa
        call_command('reset_db', '--noinput', verbosity=2)

        self.assertEqual("Reset successful.\n", m_stdout.getvalue())
        m_unlink.assert_called_once_with('test_db.sqlite3')

    @patch('sys.stdout', new_callable=StringIO)
    @patch.object(os, 'unlink', side_effect=[OSError, ])
    def test_should_print_successful_message_even_if_unlink_failed(self, m_unlink, m_stdout):  # noqa
        call_command('reset_db', '--noinput', verbosity=2)

        self.assertEqual("Reset successful.\n", m_stdout.getvalue())
        m_unlink.assert_called_once_with('test_db.sqlite3')


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_db',
        'USER': 'foo',
        'PASSWORD': 'bar',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
})
class ResetDbMysqlTests(TestCase):
    """Tests for reset_db command and mysql engine."""

    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.reset_db.input')
    def test_should_cancel_reset_db_if_input_is_different_than_yes(self, m_input, m_stdout):  # noqa
        m_input.return_value = 'no'

        call_command('reset_db')

        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_drop_and_create_database_with_characterset_utf8_and_print_success_messsage(self, m_stdout):  # noqa
        m_database = MagicMock()
        m_connection = Mock()
        m_database.connect.return_value = m_connection
        expected_calls = [
            call('DROP DATABASE IF EXISTS `test_db`'),
            call('CREATE DATABASE `test_db` CHARACTER SET utf8')
        ]

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('reset_db', '--noinput', verbosity=2)

        m_database.connect.assert_called_once_with(
            host='127.0.0.1', passwd='bar', user='foo')
        m_connection.query.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual("Reset successful.\n", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test_db',
            'USER': 'foo',
            'PASSWORD': 'bar',
            'HOST': '/var/run/mysqld/mysql.sock',
            'PORT': '3306',
        },
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_drop_and_create_database_without_characterset_and_print_success_messsage(self, m_stdout):  # noqa
        m_database = MagicMock()
        m_connection = Mock()
        m_database.connect.return_value = m_connection
        expected_calls = [
            call('DROP DATABASE IF EXISTS `test_db`'),
            call('CREATE DATABASE `test_db`')
        ]

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('reset_db', '--noinput', '--no-utf8', verbosity=2)

        m_database.connect.assert_called_once_with(
            passwd='bar', port=3306, unix_socket='/var/run/mysqld/mysql.sock',
            user='foo')
        m_connection.query.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual("Reset successful.\n", m_stdout.getvalue())


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test_db',
        'USER': 'foo',
        'PASSWORD': 'bar',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
})
class ResetDbPostgresqlTests(TestCase):
    """Tests for reset_db command and sqlite3 engine."""

    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.reset_db.input')
    def test_should_cancel_reset_db_if_input_is_different_than_yes(self, m_input, m_stdout):  # noqa
        m_input.return_value = 'no'
        call_command('reset_db')
        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_drop_and_create_database_and_print_success_messsage(self, m_stdout):  # noqa
        m_database = MagicMock()
        m_cursor = Mock()
        m_database.connect.return_value.cursor.return_value = m_cursor
        expected_calls = [
            call('DROP DATABASE "test_db";'),
            call('CREATE DATABASE "test_db" WITH OWNER = "foo"  ENCODING = \'UTF8\';')  # noqa
        ]

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('reset_db', '--noinput', verbosity=2)

        m_database.connect.assert_called_once_with(
            database='template1', host='127.0.0.1', password='bar',
            port='5432', user='foo')

        m_cursor.execute.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual("Reset successful.\n", m_stdout.getvalue())

    @override_settings(DEFAULT_TABLESPACE='TEST_TABLESPACE')
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_drop_create_database_close_sessions_and_print_success_messsage(self, m_stdout):  # noqa
        m_database = MagicMock()
        m_cursor = Mock()
        m_database.connect.return_value.cursor.return_value = m_cursor
        expected_calls = [
            call("\n                    SELECT pg_terminate_backend(pg_stat_activity.pid)\n                    FROM pg_stat_activity\n                    WHERE pg_stat_activity.datname = 'test_db';\n                "),  # noqa
            call('DROP DATABASE "test_db";'),
            call('CREATE DATABASE "test_db" WITH OWNER = "foo"  ENCODING = \'UTF8\' TABLESPACE = TEST_TABLESPACE;')  # noqa
        ]

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('reset_db', '--noinput', '--close-sessions',
                         verbosity=2)

        m_database.connect.assert_called_once_with(
            database='template1', host='127.0.0.1', password='bar',
            port='5432', user='foo')

        m_cursor.execute.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual("Reset successful.\n", m_stdout.getvalue())
