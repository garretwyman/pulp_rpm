# -*- coding: utf-8 -*-

from pulp_rpm.common.ids import (TYPE_ID_RPM, TYPE_ID_SRPM, TYPE_ID_DRPM, TYPE_ID_ERRATA,
                                 TYPE_ID_DISTRO, TYPE_ID_PKG_GROUP, TYPE_ID_PKG_CATEGORY,
                                 TYPE_ID_PKG_ENVIRONMENT, TYPE_ID_YUM_REPO_METADATA_FILE)


def get_formatter_for_type(type_id):
    """
    Return a method that takes one argument (a unit) and formats a short string
    to be used as the output for the unit_remove command

    :param type_id: The type of the unit for which a formatter is needed
    :type type_id: str
    """
    type_formatters = {
        TYPE_ID_RPM: _details_package,
        TYPE_ID_SRPM: _details_package,
        TYPE_ID_DRPM: _details_drpm,
        TYPE_ID_ERRATA: _details_id_only,
        TYPE_ID_DISTRO: _details_id_only,
        TYPE_ID_PKG_GROUP: _details_id_only,
        TYPE_ID_PKG_CATEGORY: _details_id_only,
        TYPE_ID_PKG_ENVIRONMENT: _details_id_only,
        TYPE_ID_YUM_REPO_METADATA_FILE: _yum_repo_metadata_name_only,
    }
    return type_formatters[type_id]


def _details_package(package):
    return '%s-%s-%s-%s' % (package['name'], package['version'], package['release'],
                            package['arch'])


def _details_drpm(drpm):
    return drpm['filename']


def _details_id_only(unit):
    return unit['id']


def _yum_repo_metadata_name_only(unit):
    return unit['data_type']
