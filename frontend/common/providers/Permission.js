import React, { Component } from 'react';
import propTypes from 'prop-types';
import PermissionsStore from '../stores/permissions-store';
import ConfigProvider from 'common/providers/ConfigProvider';

const Permission = class extends Component {
  static displayName = 'Permission'

  static propTypes = {
      id: propTypes.number.isRequired,
      level: propTypes.string.isRequired,
      children: OptionalFunc,
      permission: propTypes.string.isRequired,
  }

  constructor(props, context) {
      super(props, context);
      this.state = {};
      ES6Component(this);
  }

  componentDidMount() {
      const isLoading = !PermissionsStore.getPermissions(this.props.id, this.props.level) || !Object.keys(PermissionsStore.getPermissions(this.props.id, this.props.level)).length;
      if (isLoading) {
          AppActions.getPermissions(this.props.id, this.props.level);
      }
      this.listenTo(PermissionsStore, 'change', () => {
          this.forceUpdate();
      });
  }

  render() {
      const permission = PermissionsStore.getPermission(this.props.id, this.props.level, this.props.permission);
      const isLoading = !PermissionsStore.getPermissions(this.props.id, this.props.level) || !Object.keys(PermissionsStore.getPermissions(this.props.id, this.props.level)).length;
      return this.props.children({ permission, isLoading }) || <div/>;
  }
};

module.exports = ConfigProvider(Permission);
