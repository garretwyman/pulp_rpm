# Copyright (c) 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from gettext import gettext as _

from pulp.client.commands import options
from pulp.client.commands.repo.sync_publish import RunPublishRepositoryCommand
from pulp.client import parsers, validators
from pulp.client.extensions.extensions import PulpCliOption, PulpCliCommand

from pulp_rpm.common import ids, constants
from pulp_rpm.extension.admin.status import RpmExportStatusRenderer

# -- commands -----------------------------------------------------------------

DESC_EXPORT_RUN = _('triggers an immediate export of a repository')
DESC_GROUP_EXPORT_RUN = _('triggers an immediate export of a repository group')


DESC_ISO_PREFIX = _('prefix to use in the generated ISO name, default: <repo-id>-<current_date>.iso')
DESC_START_DATE = _('start date for an incremental export; only content associated with a repository'
                    ' on or after the given value will be included in the exported repository; dates '
                    'should be in standard ISO8609 format: "1970-01-01T00:00:00"')
DESC_END_DATE = _('end date for an incremental export; only content associated with a repository '
                  'on or before the given value will be included in the exported repository; dates '
                  'should be in standard ISO8609 format: "1970-01-01T00:00:00"')
DESC_EXPORT_DIR = _('the full path to a directory; if specified, the repository will be exported '
                    'to the given directory instead of being placed in ISOs and published via '
                    'HTTP or HTTPS')
DESC_ISO_SIZE = _('the maximum size, in megabytes, of the exported ISOs; if this is not '
                  'specified, DVD-sized ISOs are created')
DESC_BACKGROUND = _('if specified, the CLI process will end but the process will continue on '
                    'the server; the progress can be later displayed using the status command')
# These two flags exist because there is currently no place to configure group publishes
DESC_SERVE_HTTP = _('if this flag is used, the ISO images will be served over HTTP; if '
                    'this export is to a directory, this has no effect.')
DESC_SERVE_HTTPS = _('if this flag is used, the ISO images will be served over HTTPS; if '
                     'this export is to a directory, this has no effect.')

# Flag names, which are also the kwarg keywords
SERVE_HTTP = 'serve-http'
SERVE_HTTPS = 'serve-https'

# The iso prefix is restricted to the same character set as an id, so we use the id_validator
OPTION_ISO_PREFIX = PulpCliOption('--iso-prefix', DESC_ISO_PREFIX, required=False,
                                  validate_func=validators.id_validator)
OPTION_START_DATE = PulpCliOption('--start-date', DESC_START_DATE, required=False,
                                  validate_func=validators.iso8601_datetime_validator)
OPTION_END_DATE = PulpCliOption('--end-date', DESC_END_DATE, required=False,
                                validate_func=validators.iso8601_datetime_validator)
OPTION_EXPORT_DIR = PulpCliOption('--export-dir', DESC_EXPORT_DIR, required=False)
OPTION_ISO_SIZE = PulpCliOption('--iso-size', DESC_ISO_SIZE, required=False,
                                parse_func=parsers.parse_optional_non_negative_int)


class RpmExportCommand(RunPublishRepositoryCommand):
    def __init__(self, context):
        override_config_options = [OPTION_EXPORT_DIR, OPTION_ISO_PREFIX, OPTION_ISO_SIZE,
                                   OPTION_START_DATE, OPTION_END_DATE]

        super(RpmExportCommand, self).__init__(context=context,
                                               renderer=RpmExportStatusRenderer(context),
                                               distributor_id=ids.TYPE_ID_DISTRIBUTOR_EXPORT,
                                               description=DESC_EXPORT_RUN,
                                               override_config_options=override_config_options)


class RpmGroupExportCommand(PulpCliCommand):
    """
    The rpm group export command.
    """
    def __init__(self, context, renderer, distributor_id, name='run', description=DESC_GROUP_EXPORT_RUN):
        super(RpmGroupExportCommand, self).__init__(name, description, self.run)

        self.context = context
        self.prompt = context.prompt
        self.renderer = renderer
        self.distributor_id = distributor_id

        self.add_option(options.OPTION_GROUP_ID)
        self.add_option(OPTION_ISO_PREFIX)
        self.add_option(OPTION_ISO_SIZE)
        self.add_option(OPTION_START_DATE)
        self.add_option(OPTION_END_DATE)
        self.add_option(OPTION_EXPORT_DIR)

        self.create_flag('--serve-http', DESC_SERVE_HTTP)
        self.create_flag('--bg', DESC_BACKGROUND)

    def run(self, **kwargs):
        # Grab all the configuration options
        group_id = kwargs[options.OPTION_GROUP_ID.keyword]
        iso_prefix = kwargs[OPTION_ISO_PREFIX.keyword]
        iso_size = kwargs[OPTION_ISO_SIZE.keyword]
        start_date = kwargs[OPTION_START_DATE.keyword]
        end_date = kwargs[OPTION_END_DATE.keyword]
        export_dir = kwargs[OPTION_EXPORT_DIR.keyword]
        serve_http = kwargs[SERVE_HTTP]
        serve_https = kwargs[SERVE_HTTPS]

        # Since the export distributor is not added to a repository group on creation, add it here
        # if it is not already associated with the group id
        response = self.context.server.repo_group_distributor.distributor(group_id, self.distributor_id)
        if response.response_code == 404:
            distributor_config = {
                constants.PUBLISH_HTTP_KEYWORD: serve_http,
                constants.PUBLISH_HTTPS_KEYWORD: serve_https,
            }
            self.context.server.repo_group_distributor.create(group_id,
                                                              ids.TYPE_ID_DISTRIBUTOR_GROUP_EXPORT,
                                                              distributor_config, self.distributor_id)

        publish_config = {
            constants.PUBLISH_HTTP_KEYWORD: serve_http,
            constants.PUBLISH_HTTPS_KEYWORD: serve_https,
            constants.ISO_PREFIX_KEYWORD: iso_prefix,
            constants.ISO_SIZE_KEYWORD: iso_size,
            constants.START_DATE_KEYWORD: start_date,
            constants.END_DATE_KEYWORD: end_date,
            constants.EXPORT_DIR_KEYWORD: export_dir,
        }
        self.context.server.repo_group_actions.publish(group_id, self.distributor_id, publish_config)