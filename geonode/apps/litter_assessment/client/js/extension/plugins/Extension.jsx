/*
 * Copyright 2021, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
*/

import React from 'react';
import { connect } from 'react-redux';
import Message from "@mapstore/framework/components/I18N/Message";
import '@js/extension/assets/style.css';

function Extension() {
    return (
        <div className="extension">
            <Message msgId="extension.message" />
        </div>
    );
}

const ConnectedExtension = connect(() => ({}))(Extension);

export default {
    name: __MAPSTORE_EXTENSION_CONFIG__.name,
    component: ConnectedExtension,
    reducers: {},
    epics: {},
    containers: {}
};
