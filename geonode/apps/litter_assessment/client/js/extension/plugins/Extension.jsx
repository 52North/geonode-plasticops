import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createSelector } from 'reselect';
import { mapSelector } from '@mapstore/framework/selectors/map';

function LitterAssessment({
    center
}) {
    return (
        <div
            className="shadow"
            style={{
                position: 'absolute',
                zIndex: 100,
                bottom: 35,
                margin: 8,
                left: '50%',
                backgroundColor: '#ffffff',
                padding: 8,
                textAlign: 'center',
                transform: 'translateX(-50%)'
            }}
        >
            <div>
                <small>
                    Map Center ({center.crs})
                </small>
            </div>
            <div>
                x: <strong>{center?.x?.toFixed(6)}</strong>
                {' | '}
                y: <strong>{center?.y?.toFixed(6)}</strong>
            </div>
        </div>
    );
}

LitterAssessment.propTypes = {
    center: PropTypes.object
};

LitterAssessment.defaultProps = {
    center: {}
};

const LitterAssessmentPlugin = connect(
    createSelector([
        mapSelector
    ], (map) => ({
        center: map?.center
    })),
    {}
)(LitterAssessment);

export default {
    name: __MAPSTORE_EXTENSION_CONFIG__.name,
    component: LitterAssessmentPlugin,
    containers: {},
    epics: {},
    reducers: {}
};