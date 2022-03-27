import React from "react"
import { Table, Container } from "react-bootstrap"
import ExpandTestimony from "../ExpandTestimony/ExpandTestimony"
import { useBill, useMember } from "../db"

const MemberName = ({ memberId }) => {
  const { member, loading } = useMember(memberId)
  return <>{member?.Name}</>
}

const TestimonyRow = ({ testimony }) => {
  const { result: bill } = useBill(testimony.billId)
  const senatorId = testimony.senatorId
  const representativeId = testimony.representativeId
  return (
    <tr>
      <td>{testimony.billId}</td>
      <td>{testimony.position}</td>
      <td>
        {testimony.authorDisplayName == null
          ? "(blank)"
          : testimony.authorDisplayName}
      </td>
      <td>
        <MemberName memberId={senatorId} />
      </td>
      <td>
        <MemberName memberId={representativeId} />
      </td>
      <td>{testimony.publishedAt.toDate().toLocaleString()}</td>
      <td>{testimony.content.substring(0, 100)}...</td>
      <td>{testimony.attachment != null ? "Yes" : ""}</td>
      <td>
        <ExpandTestimony bill={bill?.content} testimony={testimony} />
      </td>
    </tr>
  )
}

const TestimonyTable = ({ testimonies }) => {
  const testimoniesComponent = testimonies.map((testimony, index) => {
    return <TestimonyRow key={index} testimony={testimony} />
  })

  return (
    <Container>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Bill</th>
            <th>Support</th>
            <th>Submitter</th>
            <th>Submitter Senator</th>
            <th>Submitter Representative</th>
            <th>Date Submitted</th>
            <th>Text</th>
            <th>Attachment?</th>
          </tr>
        </thead>
        <tbody>{testimoniesComponent}</tbody>
      </Table>
    </Container>
  )
}

export default TestimonyTable