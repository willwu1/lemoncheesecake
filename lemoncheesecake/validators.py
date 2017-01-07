'''
Created on Sep 8, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import InvalidMetadataError, ProgrammingError

__all__ = ("MetadataPolicy",)

class MetadataPolicy:
    def __init__(self):
        self._properties = {}
        self._tags = {}
        self._disallow_unknown_properties = False
        self._disallow_unknown_tags = False
    
    def has_constraints(self):
        return len(self._properties) != 0 or len(self._tags) != 0 or self._disallow_unknown_properties or self._disallow_unknown_tags
    
    def _get_rule_application(self, on_test, on_suite):
        if on_test == None and on_suite == None:
            return True, False
        if not on_test and not on_suite:
            raise ProgrammingError("either on_test or on_suite need to be True")
        return bool(on_test), bool(on_suite)
    
    def add_property_rule(self, prop_name, accepted_values=None, on_test=None, on_suite=None, required=False):
        """
        Declare a property rule with:
        - the property name
        - an optional list of accepted values
        - is the property available for tests
        - is the property available for testsuites
        - if the property is required
        If neither on_test or on_suite argument are set, then the property is only available for tests.
        """
        on_test, on_suite = self._get_rule_application(on_test, on_suite)
        self._properties[prop_name] = {
            "values": accepted_values,
            "on_test": on_test,
            "on_suite": on_suite,
            "required": required
        }
    
    def disallow_unknown_properties(self):
        """
        Disallow unknown properties for tests and testsuites.
        """
        self._disallow_unknown_properties = True
    
    def add_tag_rule(self, tag_name, on_test=None, on_suite=None):
        """
        Declare a tag constraint with:
        - the tag name
        - is the tag available for tests
        - is the tag available for testsuites
        If neither on_test or on_suite argument are set, then the tag is only available for tests.
        """
        tag_names = tag_name if type(tag_name) in (list, tuple) else [tag_name]
        for tag_name in tag_names:
            on_test, on_suite = self._get_rule_application(on_test, on_suite)
            self._tags[tag_name] = {
                "on_test": on_test,
                "on_suite": on_suite
            }
    
    def disallow_unknown_tags(self):
        """
        Disallow unknown tags for tests and testsuites.
        """
        self._disallow_unknown_tags = True

    def _check_compliance(self, obj, obj_type,
                          available_properties, forbidden_properties, 
                          available_tags, forbidden_tags):
        # check unknown properties
        if self._disallow_unknown_properties:
            for property_name in obj.properties.keys():
                if not property_name in available_properties:
                    raise InvalidMetadataError(
                        "cannot load %s '%s', the property '%s' is not supported (available are: %s)" % (
                        obj_type, obj.id, property_name, ", ".join(available_properties.keys())
                    ))
        
        # check forbidden properties
        for property_name in obj.properties.keys():
            if property_name in forbidden_properties:
                raise InvalidMetadataError(
                    "cannot load %s '%s', the property '%s' is not accepted on a %s" % (
                        obj_type, obj.id, property_name, obj_type
                    )
                )
        
        # check required properties
        for required_property in filter(lambda p: available_properties[p]["required"], available_properties.keys()):
            if not required_property in obj.properties.keys():
                raise InvalidMetadataError(
                    "cannot load %s '%s', the mandatory property '%s' is missing" % (
                    obj_type, obj.id, required_property
                ))
        
        # check properties allowed values
        for name, value in obj.properties.items():
            if name not in available_properties:
                continue
            if available_properties[name]["values"] and not value in available_properties[name]["values"]:
                raise InvalidMetadataError(
                    "cannot load %s '%s', value '%s' of property '%s' is not among accepted values: %s" % (
                    obj_type, obj.id, value, name, available_properties[name]["values"]
                ))
        
        # check unknown tags
        if self._disallow_unknown_tags:
            for tag in obj.tags:
                if tag not in available_tags.keys():
                    raise InvalidMetadataError(
                        "cannot load %s '%s', the tag '%s' is not supported (available are: %s)" % (
                        obj_type, obj.id, tag, ", ".join(available_tags)
                    ))
        
        # check forbidden tags
        for tag in obj.tags:
            if tag in forbidden_tags:
                raise InvalidMetadataError(
                    "cannot load %s '%s', the tag '%s' is not accepted on a %s" % (
                        obj_type, obj.id, tag, obj_type
                    )
                )
    
    def check_test_compliance(self, test):
        """
        Check if the test complies to the metadata policy.
        Raise ProgrammingError if not compliant.
        """
        self._check_compliance(
            test, "test", 
            {prop_name: p for prop_name, p in self._properties.items() if p["on_test"]},
            [prop_name for prop_name, p in self._properties.items() if not p["on_test"]],
            {tag_name: t for tag_name, t in self._tags.items() if t["on_test"]},
            [tag_name for tag_name, t in self._tags.items() if not t["on_test"]]
        )

    def check_suite_compliance(self, suite):
        """
        Check if the suite complies to the metadata policy.
        The method is not recursive: the tests and sub suites contained in the given suite are not checked.
        Raise ProgrammingError if not compliant.
        """
        self._check_compliance(
            suite, "suite", 
            {prop_name: p for prop_name, p in self._properties.items() if p["on_suite"]},
            [prop_name for prop_name, p in self._properties.items() if not p["on_suite"]],
            {tag_name: t for tag_name, t in self._tags.items() if t["on_suite"]},
            [tag_name for tag_name, t in self._tags.items() if not t["on_suite"]]
        )