"""
This module provides an abstraction for Module Stores that support Draft and Published branches.
"""

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from . import ModuleStoreEnum


class ModuleStoreDraftAndPublished(object):
    """
    A mixin for a read-write database backend that supports two branches, Draft and Published, with
    options to prefer Draft and fallback to Published.
    """
    __metaclass__ = ABCMeta
    BRANCH_SETTING_FUNC_KEY = 'branch_setting_func'

    def __init__(self, *args, **kwargs):
        super(ModuleStoreDraftAndPublished, self).__init__(*args, **kwargs)
        self.request_cache = kwargs.get('request_cache', None)
        self.default_branch_setting_func = kwargs.pop(self.BRANCH_SETTING_FUNC_KEY, lambda: ModuleStoreEnum.Branch.published_only)

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):
        """
        A context manager for temporarily setting a store's branch value
        """
        if self.request_cache is None:
            raise ValueError("Must have provided a request_cache in order to use the branch_setting contextmanager.")

        previous_branch_setting_func = self.request_cache.data.get(self.BRANCH_SETTING_FUNC_KEY, None)
        try:
            self.request_cache.data[self.BRANCH_SETTING_FUNC_KEY] = lambda: branch_setting
            yield
        finally:
            self.request_cache.data[self.BRANCH_SETTING_FUNC_KEY] = previous_branch_setting_func

    def get_branch_setting(self):
        """
        Returns the current branch_setting on the store.

        Returns the setting cached in the request cache, if set.
        Otherwise, returns the value of the setting function defaulted during the store's initialization.
        """
        # first check the request cache
        if self.request_cache and self.request_cache.data.get(self.BRANCH_SETTING_FUNC_KEY, None):
            return self.request_cache.data[self.BRANCH_SETTING_FUNC_KEY]()
        else:
            # return the default value
            return self.default_branch_setting_func()

    @abstractmethod
    def delete_item(self, location, user_id, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_parent_location(self, location, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def has_changes(self, usage_key):
        raise NotImplementedError

    @abstractmethod
    def publish(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def unpublish(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def revert_to_published(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def compute_publish_state(self, xblock):
        raise NotImplementedError

    @abstractmethod
    def convert_to_draft(self, location, user_id):
        raise NotImplementedError
