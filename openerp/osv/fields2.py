# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 OpenERP (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

""" High-level objects for fields. """

from copy import copy

from openerp.tools import float_round, ustr


class MetaField(type):
    """ Metaclass for field classes. """
    _class_by_type = {}

    def __init__(cls, name, bases, attrs):
        super(MetaField, cls).__init__(name, bases, attrs)
        if cls.type:
            cls._class_by_type[cls.type] = cls


class Field(object):
    """ Base class of all fields. """
    __metaclass__ = MetaField

    name = None                 # name of the field
    model = None                # name of the model of this field
    type = None                 # type of the field (string)

    store = True                # whether the field is stored in database
    compute = None              # name of model method that computes value
    depends = ()                # collection of field dependencies

    string = None               # field label
    help = None                 # field tooltip
    readonly = False
    required = False

    # attributes passed when converting from/to a column
    _attrs = ('string', 'help', 'readonly', 'required')

    def __init__(self, **kwargs):
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

    def copy(self):
        """ make a copy of `self` (used for field inheritance among models) """
        return copy(self)

    def set_model_name(self, model, name):
        """ assign the model and field names of `self` """
        self.model = model
        self.name = name
        if not self.string:
            self.string = name.replace('_', ' ').capitalize()

    @classmethod
    def from_column(cls, column):
        """ return a field for the low-level field `column` """
        if cls is Field:
            # delegate to the Field subclass corresponding to the column type
            if column._type in cls._class_by_type:
                return cls._class_by_type[column._type].from_column(column)
            else:
                raise NotImplementedError()
        # generic implementation for subclasses
        kwargs = dict((attr, getattr(column, attr)) for attr in cls._attrs)
        return cls(**kwargs)

    def to_column(self):
        """ return a low-level field object corresponding to `self` """
        kwargs = dict((attr, getattr(self, attr)) for attr in self._attrs)
        return getattr(fields, self.type)(**kwargs)

    def __get__(self, instance, owner):
        """ read the value of field `self` for the record `instance` """
        if instance is None:
            return self         # the field is accessed through the class owner
        assert instance._name == self.model
        return instance._get_field(self.name)

    def __set__(self, instance, value):
        """ set the value of field `self` for the record `instance` """
        assert instance._name == self.model
        return instance._set_field(self.name, self.record_to_cache(value))

    def cache_to_record(self, value):
        """ convert `value` from the cache level to the record level """
        return value

    def record_to_cache(self, value):
        """ convert `value` from the record level to the cache level """
        return value

    def null(self):
        """ return the null value for this field at the record level """
        return False

    def format_read(self, value):
        """ convert the record-level value as returned by method
            :meth:`openerp.osv.orm.BaseModel.read`
        """
        return value


class Boolean(Field):
    """ Boolean field. """
    type = 'boolean'

    def record_to_cache(self, value):
        return bool(value)


class Integer(Field):
    """ Integer field. """
    type = 'integer'

    def record_to_cache(self, value):
        return int(value or 0)


class Float(Field):
    """ Float field. """
    type = 'float'
    digits = None                       # None, (precision, scale), or callable
    _attrs = ('string', 'help', 'readonly', 'required', 'digits')

    @classmethod
    def from_column(cls, column):
        column.digits_change(scope.cr)      # determine column.digits
        kwargs = dict((attr, getattr(column, attr)) for attr in cls._attrs)
        return cls(**kwargs)

    def to_column(self):
        if callable(self.digits):
            self.digits = self.digits(scope.cr)
        return super(Float, self).to_column()

    def record_to_cache(self, value):
        # apply rounding here, otherwise value in cache may be wrong!
        if self.digits:
            return float_round(float(value or 0.0), precision_digits=self.digits[1])
        else:
            return float(value or 0.0)


class Char(Field):
    """ Char field. """
    type = 'char'
    size = None
    _attrs = ('string', 'help', 'readonly', 'required', 'size')

    def record_to_cache(self, value):
        return bool(value) and ustr(value)[:self.size]


class Text(Field):
    """ Text field. """
    type = 'text'


class Html(Field):
    """ Html field. """
    type = 'html'


class Date(Field):
    """ Date field. """
    type = 'date'


class Datetime(Field):
    """ Datetime field. """
    type = 'datetime'


# imported here to avoid dependency cycle issues
from openerp.osv import fields
from openerp.osv.scope import proxy as scope
