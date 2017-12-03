import * as React from 'react';

interface Props {
    attachment: AttachmentData,
    expanded: boolean
}

class Attachment extends React.Component<Props, {}> {
    render() {
        const attachment = this.props.attachment;

        return (
            <tr className="step_entry attachment" style={{display: this.props.expanded ? "" : "none"}}>
                <td className="text-uppercase text-info">ATTACHMENT</td>
                <td colSpan={3}>
                    <a href={attachment.filename} target="_blank">{attachment.description}</a>
                </td>
            </tr>
        )
    }
}

export default Attachment;