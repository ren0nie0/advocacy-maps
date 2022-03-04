import React, {useState} from "react";
import { Button, Modal } from 'react-bootstrap'
import BillHistory from "../BillHistory/BillHistory";

const BillStatus = (props) => {
  const bill = props.bill
  const [showBillStatus, setShowBillStatus] = useState(false);

  const handleShowBillStatus = () => setShowBillStatus(true);
  const handleCloseBillStatus = () => setShowBillStatus(false);

    return (
  <>
      <Button variant="primary" className="m-1" onClick={handleShowBillStatus}>
        Status
      </Button>
      <Modal show={showBillStatus} onHide={handleCloseBillStatus} size="lg">
        <Modal.Header closeButton onClick={handleCloseBillStatus}>
            <Modal.Title>{bill ? bill.BillNumber : ""}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <>
            <div className="text-center">
              Bill Status
            </div>
            <div className=" d-flex justify-content-center">
              <BillHistory bill={bill} />
            </div>
          </>
        </Modal.Body>
      </Modal>
    </>
    )
}

export default BillStatus